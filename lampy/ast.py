# coding: utf-8

from sympy import Symbol, Tuple, Dict, Lambda

from pyccel.ast.basic import Basic
from pyccel.ast.core  import FunctionCall, FunctionDef
from pyccel.codegen.utilities import random_string

#=========================================================================
class BasicMap(Basic):
    """."""
    _name = 'BasicMap'

    def __new__( cls, func, target ):

        if not isinstance(target, (list, tuple, Tuple)):
            target = [target]

        target = Tuple(*target)

        obj = Basic.__new__(cls, func, target)
        obj._tag = random_string( 4 )

        return obj

    @property
    def func(self):
        return self._args[0]

    @property
    def target(self):
        return self._args[1]

    @property
    def tag(self):
        return self._tag

    @property
    def name(self):
        return '{name}_{tag}'.format(name=self._name, tag=self.tag)


class Map(BasicMap):
    _name = 'map'

    pass

class ProductMap(BasicMap):
    _name = 'xmap'

    pass

class TensorMap(BasicMap):
    _name = 'tmap'

    pass

#=========================================================================
class Zip(Basic):
    def __new__( cls, *target ):
        target = Tuple(*target)
        obj = Basic.__new__(cls, target)
        obj._name = 'zip_{}'.format( random_string( 4 ) )
        return obj

    @property
    def arguments(self):
        return self._args[0]

    @property
    def name(self):
        return self._name

    def __len__(self):
        return len(self.arguments)

#=========================================================================
class Product(Basic):
    def __new__( cls, *target ):
        target = Tuple(*target)
        obj = Basic.__new__(cls, target)
        obj._name = 'product_{}'.format( random_string( 4 ) )
        return obj

    @property
    def arguments(self):
        return self._args[0]

    @property
    def name(self):
        return self._name

    def __len__(self):
        return len(self.arguments)

#=========================================================================
class BasicReduce(Basic):
    """."""
    def __new__( cls, target ):

        obj = Basic.__new__(cls, target)
        obj._name = 'reduce_{}'.format( random_string( 4 ) )
        return obj

    @property
    def target(self):
        return self._args[0]

    @property
    def name(self):
        return self._name


class AddReduce(BasicReduce):
    pass

class MulReduce(BasicReduce):
    pass

#==========================================================================
# any argument
class AnyArgument(Symbol):
    pass

#==========================================================================
# this is a hack since xreplace returns an error when it finds sympy.core.function.UndefinedFunction
# TODO see if future versions of sympy will fix this problem
#(found with version == 1.2)
class FunctionSymbol(Symbol):

    def __call__(self, *args):
        args = Tuple(*args)
        return FunctionCall(self.name, args)

#=========================================================================
class PartialFunction(Basic):
    """."""
    def __new__( cls, func, target ):

        assert(isinstance( func, FunctionSymbol ))
        assert(isinstance( target, Dict ))

        obj = Basic.__new__( cls, func, target )

        tag = random_string( 4 )
        obj._name = 'partial_{func}_{tag}'.format( func=func.name, tag=tag )
        obj._funcdef = None

        return obj

    @property
    def func(self):
        return self._args[0]

    @property
    def target(self):
        return self._args[1]

    @property
    def name(self):
        return self._name

    @property
    def funcdef(self):
        return self._funcdef

    def set_definition(self, funcdef):
        self._funcdef = funcdef

    def __call__(self, arguments):
        # ...
        if not isinstance(arguments, (list, tuple, Tuple)):
            arguments = [arguments]
        arguments = Tuple(*arguments)

        assert(len(self.target) == len(arguments))
        assert(isinstance(self.funcdef, FunctionDef))
        # ...

        # ...
        func      = self.func
        target    = self.target
        funcdef   = self.funcdef
        func_args = funcdef.arguments
        # ...

        # ...
        target_arg_names = [x.name for x in list(target.keys())]
        args = []
        current = 0
        for x in func_args:
            if x.name in target_arg_names:
                arg = [a for k,a in target.items() if k.name == x.name]
                assert(len(arg) == 1)
                arg = arg[0]

                args += [arg]

            else:
                args += [arguments[current]]
                current += 1
        # ...

        args = Tuple(*args)
        return FunctionCall(func.name, args)



#=========================================================================
class LampyLambda(Basic):

    def __new__( cls, func ):

        assert(isinstance( func, Lambda ))

        return Basic.__new__( cls, func )

    @property
    def func(self):
        return self._args[0]

#=========================================================================
class Call(Basic):

    def __new__(cls, expr, args):

        # ...
        if not isinstance(args, (tuple, list, Tuple)):
            args = [args]

        args = Tuple(*args)
        # ...

        return Basic.__new__(cls, expr, args)

    @property
    def expr(self):
        return self._args[0]

    @property
    def arguments(self):
        return self._args[1]

#=========================================================================
_map_registery = {'map': Map, 'xmap': ProductMap, 'tmap': TensorMap}

_ = AnyArgument('_')
