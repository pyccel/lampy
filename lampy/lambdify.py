# -*- coding: UTF-8 -*-

# TODO use OrderedDict when possible
#      right now namespace used only globals, => needs to look in locals too

import os
import sys
import inspect
import importlib
import numpy as np
from types import FunctionType

#from sympy import Indexed, IndexedBase, Tuple, Lambda
#from sympy.core.function import AppliedUndef
#from sympy.core.function import UndefinedFunction
#from sympy import sympify
#from sympy import Dummy

#from pyccel.codegen.utilities import construct_flags as construct_flags_pyccel
#from pyccel.codegen.utilities import execute_pyccel
#from pyccel.codegen.utilities import get_source_function
#from pyccel.codegen.utilities import random_string
#from pyccel.codegen.utilities import write_code
#from pyccel.codegen.utilities import mkdir_p
#from pyccel.ast.datatypes import dtype_and_precsision_registry as dtype_registry
#from pyccel.ast import Variable, Len, Assign, AugAssign
#from pyccel.ast import For, Range, FunctionDef
#from pyccel.ast import FunctionCall
#from pyccel.ast import Comment, AnnotatedComment
#from pyccel.ast import Import
#from pyccel.ast.core import Slice, String
#from pyccel.ast import Zeros
#from pyccel.ast.datatypes import NativeInteger, NativeReal, NativeComplex, NativeBool
from pyccel.codegen.printing.pycode import pycode
#from pyccel.codegen.printing.fcode  import fcode
#from pyccel.ast.utilities import build_types_decorator
#from pyccel.ast.datatypes import get_default_value
from pyccel.parser.parser import Parser as PyccelParser

from lampy.syntax    import parse as parse_lambda
from lampy.semantic  import Parser as SemanticParser
from lampy.codegen   import AST
from lampy.utilities import get_decorators
from lampy.utilities import get_pyccel_imports_code
from lampy.utilities import get_dependencies_code
from lampy.utilities import math_atoms_as_str
from lampy.printing  import pycode
from lampy.interface import LambdaInterface
from os import path
from pyccel.ast.basic import Basic
from sympy import Integral, Symbol, Tuple
from sympy.utilities.iterables import iterable

#==============================================================================
class AsName(Basic):
    def __new__(cls, name, target):

        # TODO check

        return Basic.__new__(cls, name, target)

    @property
    def name(self):
        return self._args[0]

    @property
    def target(self):
        return self._args[1]

    def _sympystr(self, printer):
        sstr = printer.doprint
        return '{0} as {1}'.format(sstr(self.name), sstr(self.target))

#==============================================================================
class DottedName(Basic):
    def __new__(cls, *args):
        return Basic.__new__(cls, *args)

    @property
    def name(self):
        return self._args

    def __str__(self):
        return """.""".join(str(n) for n in self.name)

    def _sympystr(self, printer):
        sstr = printer.doprint
        return """.""".join(sstr(n) for n in self.name)



#==============================================================================
class Import(Basic):

    def __new__(cls, target, source=None):

        def _format(i):
            if isinstance(i, str):
                if '.' in i:
                    return DottedName(*i.split('.'))
                else:
                    return Symbol(i)
            if isinstance(i, (DottedName, AsName)):
                return i
            elif isinstance(i, Symbol):
                return i
            else:
                raise TypeError('Expecting a string, Symbol DottedName, given {}'.format(type(i)))

        _target = []
        if isinstance(target, (str, Symbol, DottedName, AsName)):
            _target = [_format(target)]
        elif iterable(target):
            for i in target:
                _target.append(_format(i))
        target = Tuple(*_target, sympify=False)

        if not source is None:
            source = _format(source)

        return Basic.__new__(cls, target, source)

    @property
    def target(self):
        return self._args[0]

    @property
    def source(self):
        return self._args[1]

    def _sympystr(self, printer):
        sstr = printer.doprint
        target = ', '.join([sstr(i) for i in self.target])
        if self.source is None:
            return 'import {target}'.format(target=target)
        else:
            source = sstr(self.source)
            return 'from {source} import {target}'.format(source=source,
                    target=target)
#==============================================================================

def get_source_function(func):
    if not callable(func):
        raise TypeError('Expecting a callable function')

    lines = inspect.getsourcelines(func)
    lines = lines[0]
    # remove indentation if the first line is indented
    a = lines[0]
    leading_spaces = len(a) - len(a.lstrip())
    code = ''
    for a in lines:
        if leading_spaces > 0:
            line = a[leading_spaces:]
        else:
            line = a
        code = '{code}{line}'.format(code=code, line=line)

    return code

#==============================================================================
def write_code(filename, code, folder=None):
    if not folder:
        folder = os.getcwd()
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        raise ValueError('{} folder does not exist'.format(folder))
    filename = os.path.basename( filename )
    filename = os.path.join(folder, filename)
    # TODO check if init exists
    # add __init__.py for imports
    cmd = 'touch {}/__init__.py'.format(folder)
    os.system(cmd)
    f = open(filename, 'w')
    for line in code:
        f.write(line)
    f.close()
    return filename
#==============================================================================
def mkdir_p(dir):
    # type: (unicode) -> None
    if path.isdir(dir):
        return
    os.makedirs(dir)
#==============================================================================
_accelerator_registery = {'openmp':  'omp',
                          'openacc': 'acc',
                          None:      None}

#==============================================================================
def _parse_typed_functions(user_functions):
    """generate ast for dependencies."""
    code  = get_pyccel_imports_code()
    code += get_dependencies_code(user_functions)
    pyccel = PyccelParser(code)
    ast = pyccel.parse()
    settings = {}
    ast = pyccel.annotate(**settings)
    return ast.namespace.functions

#==============================================================================
def _lambdify(func, namespace={}, **kwargs):

    if not isinstance(func, FunctionType):
        raise TypeError('Expecting a lambda function')

    # ... get the function source code
    func_code = get_source_function(func)
    # ...

    # ...
    syntax_only = kwargs.pop('syntax_only', False)
    L = parse_lambda(func_code)

    if syntax_only:
        return L
    # ...

    # ... TODO move this to semantic parser
    user_functions = {}
    for f_name, f in namespace.items():

        # ... check if a user function
        decorators = get_decorators(f)
        if f_name in decorators.keys():
            decorators = decorators[f_name]
            if 'types' in decorators:
                # TODO
                f_symbolic = f
                user_functions[f_name] = f_symbolic
                setattr(f_symbolic, '_imp_', f)

            else:
                raise ValueError('{} given without a type'.format(f_name))

        else:
            raise NotImplementedError('')

    typed_functions = _parse_typed_functions(list(user_functions.values()))
    # ...

    # ... semantic analysis
    semantic_only = kwargs.pop('semantic_only', False)
    parser = SemanticParser(L, typed_functions=typed_functions)
    dtype = parser.doit()

#    ######### DEBUG
#    print('=======================')
#    parser.inspect()
#    print('=======================')

    if semantic_only:
        return dtype
    # ...

    # ... ast
    ast_only = kwargs.pop('ast_only', False)
    ast = AST(parser, **kwargs)
    func = ast.doit()

    with_interface = len(func.m_results) > 0

    if ast_only:
        return func
    # ...

    # ... printing of a python function without interface
    printing_only = kwargs.pop('printing_only', False)
    if printing_only:
        return pycode(func)
    # ...

    # ...
    imports = []
    # ...

    # ... get math functions and constants
    math_elements = math_atoms_as_str(func)
    math_imports = []
    for e in math_elements:
        math_imports += [Import(e, 'numpy')]

    imports += math_imports

    # convert to a string
    imports = '\n'.join([pycode(i) for i in imports])
    # ...

    # ... print python code
    code  = get_pyccel_imports_code()
    code += '\n' + imports + '\n'
    code += get_dependencies_code(list(user_functions.values()))
    code += '\n\n'
    code += pycode(func)
    # ...

    # ...
    folder = kwargs.pop('folder', None)
    if folder is None:
        basedir = os.getcwd()
        folder = '__pycache__'
        folder = os.path.join( basedir, folder )

    folder = os.path.abspath( folder )
    mkdir_p(folder)
    # ...

    # ...
    func_name   = str(func.name)

    module_name = 'mod_{}'.format(func_name)
    write_code('{}.py'.format(module_name), code, folder=folder)
#    print(code)
#    sys.exit(0)

    sys.path.append(folder)
    package = importlib.import_module( module_name )
    sys.path.remove(folder)
    # ...

    # we return a module, that will processed by epyccel

    # ... module case
    from pyccel.epyccel import epyccel
    accelerator = kwargs.pop('accelerator', None)
    verbose     = kwargs.pop('verbose', False)
#    verbose     = kwargs.pop('verbose', True)

    f2py_package = epyccel ( package, accelerator = accelerator, verbose = verbose )
    f2py_func_name = func_name
    f2py_func = getattr(f2py_package, f2py_func_name)

#    ####### DEBUG
#    return f2py_func

    if not func.is_procedure:
        return f2py_func
    # ...

    # ..............................................
    #     generate a python interface
    # ..............................................
    f2py_module_name = os.path.basename(f2py_package.__file__)
    f2py_module_name = os.path.splitext(f2py_module_name)[0]

    # ... create a python interface with an optional 'out' argument
    #     à la numpy
    interface = LambdaInterface(func, Import(f2py_func_name, f2py_module_name))
    # ...

    # ...
    code = pycode(interface)
#    print(code)
    # ...

    # ...
    func_name = str(interface.name)
    # ...

    # TODO this is a temporary fix
    g = {}
    exec(code, g)
    f = g[func_name]
    return f
