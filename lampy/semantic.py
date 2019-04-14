# coding: utf-8

import os
from os.path import join, dirname

from sympy import Symbol, Lambda, Function, Dummy
from sympy import Tuple, IndexedBase
from sympy.core.function import AppliedUndef
from sympy.core.function import UndefinedFunction
from sympy import Integer, Float
from sympy import sympify
from sympy import FunctionClass


from pyccel.codegen.utilities import random_string
from pyccel.ast.utilities import build_types_decorator
from pyccel.ast.datatypes import Int, Real, Complex, Bool
from pyccel.ast.core import Slice
from pyccel.ast.core import Variable, FunctionDef, Assign, AugAssign
from pyccel.ast.core import Return
from pyccel.ast.basic import Basic

from .datatypes import assign_type, BasicTypeVariable
from .datatypes import TypeVariable, TypeTuple, TypeList, TypeFunction
from .lexeme    import _internal_map_functors
from .lexeme    import _internal_functors
from .lexeme    import _internal_zip_functions
from .lexeme    import _internal_product_functions
from .lexeme    import _internal_applications
from .lexeme    import _elemental_math_functions
from .lexeme    import _math_vector_functions
from .lexeme    import _math_matrix_functions
from .lexeme    import _math_functions
from .ast       import Map, ProductMap, TensorMap, Zip, Product
from .ast       import BasicReduce, AddReduce, MulReduce
from .ast       import BasicMap
from .ast       import PartialFunction
from .ast       import LampyLambda


#=========================================================================
def sanitize(expr):
    if isinstance(expr, Lambda):
        args = expr.variables
        expr = sanitize(expr.expr)

        return Lambda(args, expr)

    elif isinstance(expr, AppliedUndef):
        name = expr.__class__.__name__

        args = [sanitize(i) for i in expr.args]
        # first argument of Map & Reduce are functions
        if name in _internal_functors:
            first = args[0]
            if isinstance(first, Symbol):
                args[0] = Function(first.name)

        else:
            return Function(name)(*args)

    elif isinstance(expr, (int, float, Integer, Float, Symbol)):
        return expr

    else:
        raise TypeError('Not implemented for {}'.format(type(expr)))


#=========================================================================
# TODO add some verifications before starting annotating L
class Parser(object):

    def __init__(self, expr, **kwargs):
        assert(isinstance(expr, Lambda))

        self._expr = LampyLambda( expr )

        # ...
        self._d_types   = {}
        self._d_domain_types   = {} # for each codomain we store its associated domain type
        self._d_expr    = {}
        self._tag       = random_string( 8 )

        # TODO to be removed later?
        self._d_functions = {}

        # to store current typed expr
        # this must not be a private variable,
        # in order to modify it on the fly
        self.main = self.expr
        self.main_type = None
        # ...

        # ... add types for arguments and results
        #     TODO use domain and codomain optional args for functions
        self._typed_functions = kwargs.pop('typed_functions', {})
        for f in self.typed_functions.values():
            type_domain   = assign_type( f.arguments )
            type_codomain = assign_type( f.results )

            self._set_type( f, value = type_domain,    domain = True )
            self._set_type( f, value = type_codomain, codomain = True )
            self._set_domain_type( type_domain, type_codomain )
            self._insert_function( f, type_domain, type_codomain )
        # ...

        # ... default Type
        prefix = kwargs.pop('prefix', 'd') # doubles as default
        dtype     = None
        precision = None
        if prefix == 'i':
            dtype     = Int
            precision = 4

        elif prefix == 's':
            dtype     = Real
            precision = 4

        elif prefix == 'd':
            dtype     = Real
            precision = 8

        elif prefix == 'c':
            dtype     = Complex
            precision = 8

        elif prefix == 'z':
            dtype     = Complex
            precision = 16

        else:
            raise ValueError('Wrong prefix. Available: i, s, d, c, z')

        var = Variable(dtype, 'dummy_' + self.tag, precision=precision)
        self._default_type = TypeVariable(var)
        # ...

        # ... get all functions
        calls = list(expr.atoms(AppliedUndef))
        map_funcs = [i.args[0] for i in calls if i.__class__.__name__ in _internal_map_functors]
        callables = [i.func for i in calls  if not i.__class__.__name__ in _internal_functors]
        functions = list(set(map_funcs + callables))

        for f in functions:
            if str(f) in _elemental_math_functions:
                type_domain   = self.default_type
                type_codomain = self.default_type

                self._set_type(f, value=type_domain, domain=True)
                self._set_type(f, value=type_codomain, codomain=True)
                self._set_domain_type(type_domain, type_codomain)
                self._insert_function( str(f), type_domain, type_codomain )

            elif not str(f) in list(_internal_applications) + list(self.typed_functions.keys()):
                raise NotImplementedError('{} not available'.format(str(f)))
        # ...

    @property
    def expr(self):
        return self._expr

    @property
    def typed_functions(self):
        return self._typed_functions

    @property
    def default_type(self):
        return self._default_type

    @property
    def d_types(self):
        return self._d_types

    @property
    def d_domain_types(self):
        return self._d_domain_types

    @property
    def d_functions(self):
        return self._d_functions

    @property
    def d_expr(self):
        return self._d_expr

    @property
    def tag(self):
        return self._tag

    def inspect(self):
        print(self.d_types)
        for k,v in self.d_types.items():
            print('  {k} = {v}'.format(k=k, v=v.view()))

        print('')

        print(self.d_domain_types)
        for k,v in self.d_domain_types.items():
            print('  {v} --> {k}'.format(k=k, v=v))

    def _get_label(self, target, domain=False, codomain=False):
        # TODO improve
        if codomain:
            assert(not domain)
            if (isinstance(target, FunctionClass)):
                name = str(target)

            else:
                name = str(target.name)

            return name

        if domain:
            assert(not codomain)
            if (isinstance(target, FunctionClass)):
                name = str(target)

            else:
                name = str(target.name)

            _avail_funcs = list(self.typed_functions.keys()) + _math_functions
            if name in _avail_funcs:
                return name + '_args'

        if isinstance(target, FunctionDef):
            return str(target.name) + '_args'

        elif isinstance(target, UndefinedFunction):
            return str(target)

        elif isinstance(target, BasicMap):
            return target.name

        elif isinstance(target, Lambda):
            if not hasattr(target, 'name'):
                raise ValueError('Expecting an attribut name')

            return target.name

        elif isinstance(target, Symbol):
            return target.name

        else:
            raise NotImplementedError('for {}'.format(type(target)))

    def _get_type(self, target, domain=False, codomain=False):
        label = self._get_label(target, domain=domain, codomain=codomain)

        if label in self.d_types.keys():
            return self.d_types[label]

        return None

    def _set_type(self, target, value, domain=False, codomain=False):
        label = self._get_label(target, domain=domain, codomain=codomain)

        self._d_types[label] = value
        self._set_expr(value, target)

    def _set_expr(self, t_var, expr):
        self._d_expr[t_var.name] = expr

    def _set_domain_type(self, type_domain, type_codomain):
        self._d_domain_types[type_codomain] = type_domain

    def _insert_function(self, f, type_domain, type_codomain):
        # ...
        if isinstance(f, FunctionDef):
            f_name = str(f.name)

        elif isinstance(f, str):
            f_name = f

        elif isinstance(f, PartialFunction):
            f_name = str(f.name)

        elif isinstance(f, Lambda):
            if not hasattr(f, 'name'):
                msg = 'Expecting {} to have a name'.format(f)
                raise AttributeError(msg)

            f_name = str(f.name)

        else:
            raise NotImplementedError('{} not available'.format(type(f)))
        # ...

        type_func = TypeFunction( type_domain, type_codomain )
        self._d_functions[f_name] = type_func

    def doit(self, verbose=False):

        # ... compute type
        i_count = 0
        max_count = 2
        while(i_count < max_count and not isinstance(self.main, BasicTypeVariable)):
            if verbose:
                print('----> BEFORE ', self.main)

            self.main = self._visit(self.main)

            if verbose:
                print('<---- AFTER', self.main)

            i_count += 1
        # ...

        return self.main

    def _visit(self, stmt, value=None):

        cls = type(stmt)
        name = cls.__name__

        method = '_visit_{}'.format(name)
        if hasattr(self, method):
            return getattr(self, method)(stmt, value=value)

        elif name in self.d_functions.keys():
            # application case
            if not isinstance( stmt, AppliedUndef ):
                raise TypeError('Expecting an application')

            # ... in the case of a typed function, we check that the number of
            #     arguments is the same as the call
            if name in self.typed_functions.keys():
                f = self.typed_functions[name]
                f_args = f.arguments
                call_args = stmt.args
                assert(len(call_args) == len(f_args))
            # ...

            # get the type of the function
            type_func = self.d_functions[name]

            return type_func.codomain

        # Unknown object, we raise an error.
        raise TypeError('{node} not yet available'.format(node=type(stmt)))

    def _visit_Lambda(self, stmt, value=None):
        # TODO treat args

        # ... treat the expression of the lambda
        expr = self._visit(stmt.expr)
        # ...

        # ...
        if isinstance( stmt.expr, AppliedUndef ):
            func_name = stmt.expr.__class__.__name__

        elif isinstance( stmt.expr, PartialFunction ):
            func_name = stmt.expr.name

        else:
            msg = '{} not available yet'.format(type(stmt.expr))
            raise NotImplementedError(msg)
        # ...

        # ...
        type_func     = self.d_functions[func_name]
        type_domain   = type_func.domain
        type_codomain = type_func.codomain
        # ...

        # ...
        self._insert_function( stmt, type_domain, type_codomain )
        # ...

        return type_codomain

    def _visit_LampyLambda(self, stmt, value=None):

        self.main = self._visit(stmt.func.expr)
        if isinstance(self.main, BasicTypeVariable):
            self.main_type = self.main
        return self.main

    def _visit_TypeVariable(self, stmt, value=None):
        return stmt

    def _visit_TypeTuple(self, stmt, value=None):
        return stmt

    def _visit_TypeList(self, stmt, value=None):
        return stmt

    def _visit_Symbol(self, stmt, value=None):
        assert(not( value is None ))
        self._set_type(stmt, value)

    def _visit_Map(self, stmt, value=None):
        func   = stmt.func
        target = stmt.target
        target = Zip(*target)

        type_codomain = self._get_type(func, codomain=True)
        type_domain   = self._get_type(func, domain=True)

        if not type_codomain:
            expr = self._visit(func)

            type_func = self.d_functions[func.name]
            type_domain = type_func.domain
            type_codomain = type_func.codomain

            if not type_codomain:
                print('> Unable to compute type for {} '.format(stmt))
                raise NotImplementedError('')

        type_domain   = TypeList(type_domain)
        type_codomain = TypeList(type_codomain)
        self._set_domain_type(type_domain, type_codomain)
        self._insert_function( stmt.name, type_domain, type_codomain )

        self._visit(target, value=type_domain)
        self._set_expr(type_codomain, stmt)

        return type_codomain

    def _visit_ProductMap(self, stmt, value=None):
        func   = stmt.func
        target = stmt.target
        target = Product(*target)

        type_codomain = self._get_type(func, codomain=True)
        type_domain   = self._get_type(func, domain=True)

        if not type_codomain:
            print('> Unable to compute type for {} '.format(stmt))
            raise NotImplementedError('')

        type_domain   = TypeList(type_domain)
        type_codomain = TypeList(type_codomain)
        self._set_domain_type(type_domain, type_codomain)
        self._insert_function( stmt.name, type_domain, type_codomain )

        self._visit(target, value=type_domain)
        self._set_expr(type_codomain, stmt)

        return type_codomain

    def _visit_TensorMap(self, stmt, value=None):
        func   = stmt.func
        target = stmt.target
        target = Product(*target)

        type_codomain = self._get_type(func, codomain=True)
        type_domain   = self._get_type(func, domain=True)

        if not type_codomain:
            print('> Unable to compute type for {} '.format(stmt))
            raise NotImplementedError('')

        # TODO check that rank is the same for all domain
        for i in range(0, len(target.arguments)):
            type_domain   = TypeList(type_domain)
            type_codomain = TypeList(type_codomain)

        self._set_domain_type(type_domain, type_codomain)
        self._insert_function( stmt.name, type_domain, type_codomain )

        self._visit(target, value=type_domain)
        self._set_expr(type_codomain, stmt)

        return type_codomain

    def _visit_Zip(self, stmt, value=None):
        arguments = stmt.arguments

        assert(not( value is None ))
        assert(isinstance(value, TypeList))

        # ...
        if isinstance(value.parent, TypeVariable):
            values = [value.parent]

        elif isinstance(value.parent, TypeTuple):
            values = value.types.types

        elif isinstance(value.parent, TypeList):
            values = [value.parent]

        else:
            msg = '{} not available yet'.format(type(value.parent))
            raise NotImplementedError(msg)
        # ...

        # ...
        for a,t in zip(arguments, values):
            type_domain  = TypeList(t)
            self._visit(a, value=type_domain)
        # ...

        type_codomain = value
        self._set_domain_type(value, type_codomain)
        self._insert_function( stmt.name, value, type_codomain )

#        # update main expression
#        print(self.main)
#        print(stmt)
#        print(type_codomain)
##        import sys; sys.exit(0)
#        self.main = self.main.xreplace({stmt: type_codomain})
        self._set_expr(type_codomain, stmt)

        return type_codomain

    def _visit_Product(self, stmt, value=None):
        arguments = stmt.arguments

        assert(not( value is None ))
        assert(isinstance(value, TypeList))

#        # TODO add this check only when using tmap
#        assert(len(value) == len(arguments))

        values = value.types.types

        for a,t in zip(arguments, values):
            type_domain  = TypeList(t)
            self._visit(a, value=type_domain)

        type_codomain = value
        self._set_domain_type(value, type_codomain)
        self._insert_function( stmt.name, value, type_codomain )

        # update main expression
        self.main = self.main.xreplace({stmt: type_codomain})
        self._set_expr(type_codomain, stmt)

        return type_codomain

    def _visit_AddReduce(self, stmt, value=None):
        return self._visit_Reduce( stmt, value=value, op='+' )

    def _visit_MulReduce(self, stmt, value=None):
        return self._visit_Reduce( stmt, value=value, op='*' )

    def _visit_Reduce(self, stmt, value=None, op=None):

        target = stmt.target

        type_codomain = self._visit(target)
        assert( isinstance( type_codomain, TypeList ) )
        type_codomain = type_codomain.types

        type_domain   = self.d_domain_types[type_codomain]

        type_domain   = TypeList(type_domain)
        type_codomain = type_codomain.duplicate()
        self._set_domain_type(type_domain, type_codomain)
        self._insert_function( stmt.name, type_domain, type_codomain )

        self._visit(target, value=type_domain)
        self._set_expr(type_codomain, stmt)

        return type_codomain

    def _visit_PartialFunction(self, stmt, value=None):
        func   = stmt.func
        target = stmt.target

        # ...
        if not func.name in self.typed_functions.keys():
            raise ValueError('{} is not a typed function'.format(func.name))

        funcdef = self.typed_functions[func.name]
        func_args = funcdef.arguments
        stmt.set_definition(funcdef)
        # ...

        # ... get the codomain of the function
        if not func.name in self.d_functions.keys():
            raise ValueError('{} type not available'.format(func.name))

        t_func        = self.d_functions[func.name]
        type_codomain = t_func.codomain
        # ...

        # ...
        target_arg_names = [i.name for i in list(target.keys())]
        newargs = [i for i in func_args if not i.name in target_arg_names]
        # ...

        # ... assign domain type from new arguments
        type_domain = assign_type( newargs )
        # ...

        # ...
        self._insert_function( stmt, type_domain, type_codomain )
        # ...

        return type_codomain
