# coding: utf-8

import os
from os.path import join, dirname

from sympy import Symbol, Lambda, Function, Dummy
from sympy import sympify, Dict, Tuple

from textx.metamodel import metamodel_from_str

from pyccel.codegen.utilities import random_string

from .ast    import AddReduce, MulReduce, FunctionSymbol, BasicMap
from .ast    import _map_registery
from .ast    import _, AnyArgument
from .ast    import PartialFunction
from .lexeme import _internal_map_functors
from .lexeme import _internal_reduction_operators

#==========================================================================
class NamedAbstraction(object):
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')
        self.abstraction = kwargs.pop('abstraction')

class Abstraction(object):
    def __init__(self, **kwargs):
        self.args = kwargs.pop('args')
        self.expr = kwargs.pop('expr')

class Application(object):
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name')
        self.args = kwargs.pop('args')

class ValuedItem(object):
    def __init__(self, **kwargs):
        self.name  = kwargs.pop('name')
        self.value = kwargs.pop('value')

#==========================================================================
def to_sympy(stmt):

    if isinstance(stmt, NamedAbstraction):
        name = stmt.name
        expr = to_sympy(stmt.abstraction)
        return expr

    elif isinstance(stmt, Abstraction):
        args = [to_sympy(i) for i in stmt.args]
        expr = to_sympy(stmt.expr)

        func = Lambda(args, expr)
        # add a name for the lambda expression
        # TODO improve this by implementing a new class
        #      for Lambda in lampy
        setattr(func, 'name', 'lambda_{}'.format( random_string( 4 ) ))

        return func

    elif isinstance(stmt, Application):
        name = stmt.name
        first = to_sympy(stmt.args[0])

        if name in _internal_map_functors:
            if not isinstance( first, (Lambda, BasicMap) ):
                func_name = str(stmt.args[0])
                func      = FunctionSymbol(func_name)

            else:
                func = first

            arguments = stmt.args[1:]
            arguments = [to_sympy(i) for i in arguments]

            return _map_registery[name]( func, arguments )

        elif name == 'reduce':
            if not( len(stmt.args) == 2 ):
                raise ValueError('Wrong number of arguments for reduce')

            op        = stmt.args[0]
            if not op in _internal_reduction_operators:
                msg = "Only 'add' and 'mul' reduction operators are available"
                raise ValueError(msg)

            target = to_sympy(stmt.args[1])

            if op == 'add':
                return AddReduce( target )

            elif op == 'mul':
                return MulReduce( target )

        elif name == 'partial':
            if not isinstance( first, Lambda ):
                func_name = str(stmt.args[0])
                func      = FunctionSymbol(func_name)

            else:
                func = first

            arguments = stmt.args[1:]
            arguments = [to_sympy(i) for i in arguments]

            assert(all([isinstance(i, Tuple) for i in arguments]))

            # ...
            d = {}
            for i in arguments:
                key   = i[0]
                value = i[1]

                d[key] = value

            arguments = Dict(d)
            # ...

            return PartialFunction( func, arguments )

        else:
            args = [to_sympy(i) for i in stmt.args]

            return Function(name)(*args)

    elif isinstance(stmt, (int, float)):
        return stmt

    elif isinstance(stmt, str):
        if stmt == '_':
            return _

        else:
            return sympify(stmt)

    elif isinstance(stmt, ValuedItem):
        key   = to_sympy(stmt.name)
        value = to_sympy(stmt.value)
        return Tuple(key, value)

    else:
        raise TypeError('Not implemented for {}'.format(type(stmt)))

#==========================================================================
def parse(inputs, debug=False, verbose=False):
    this_folder = dirname(__file__)

    classes = [NamedAbstraction, Abstraction, Application, ValuedItem]

    # Get meta-model from language description
    grammar = join(this_folder, 'grammar.tx')

    from textx.metamodel import metamodel_from_file
    meta = metamodel_from_file(grammar, debug=debug, classes=classes)

    # Instantiate model
    if os.path.isfile(inputs):
        ast = meta.model_from_file(inputs)

    else:
        ast = meta.model_from_str(inputs)

    # ...
    expr = to_sympy(ast)
    if verbose:
        print('>>> stage 0 = ', expr)
    # ...

    # ...
    if verbose:
        print('')
    # ...

    return expr
