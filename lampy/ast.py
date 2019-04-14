# coding: utf-8

from sympy import Symbol, Tuple, Dict, Lambda

from pyccel.ast.basic import Basic
from pyccel.ast.core  import FunctionCall
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

#=========================================================================
class LampyLambda(Basic):

    def __new__( cls, func ):

        assert(isinstance( func, Lambda ))

        return Basic.__new__( cls, func )

    @property
    def func(self):
        return self._args[0]

#=========================================================================
_map_registery = {'map': Map, 'xmap': ProductMap, 'tmap': TensorMap}

_ = AnyArgument('_')
