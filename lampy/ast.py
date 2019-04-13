# coding: utf-8

from sympy import Symbol, Tuple

from pyccel.ast.basic import Basic
from pyccel.ast.core  import FunctionCall

#=========================================================================
class BasicMap(Basic):
    """."""

    def __new__( cls, func, target ):

        if not isinstance(target, (list, tuple, Tuple)):
            target = [target]

        target = Tuple(*target)

        return Basic.__new__(cls, func, target)

    @property
    def func(self):
        return self._args[0]

    @property
    def target(self):
        return self._args[1]

#    def _xreplace(self, rule):
#        print('PAR ICI')
#        import sys; sys.exit(0)

class Map(BasicMap):
    pass

class ProductMap(BasicMap):
    pass

class TensorMap(BasicMap):
    pass

#=========================================================================
class Zip(Basic):
    def __new__( cls, *target ):
        target = Tuple(*target)
        return Basic.__new__(cls, target)

    @property
    def arguments(self):
        return self._args[0]

    def __len__(self):
        return len(self.arguments)

#=========================================================================
class Product(Basic):
    def __new__( cls, *target ):
        target = Tuple(*target)
        return Basic.__new__(cls, target)

    @property
    def arguments(self):
        return self._args[0]

    def __len__(self):
        return len(self.arguments)

#=========================================================================
class BasicReduce(Basic):
    """."""
    def __new__( cls, target ):

        return Basic.__new__( cls, target )

    @property
    def target(self):
        return self._args[0]

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
class CurriedFunction(Basic):
    """."""
    def __new__( cls, func, target ):

        assert(isinstance( func, FunctionSymbol ))

        return Basic.__new__( cls, func, target )

    @property
    def func(self):
        return self._args[0]

    @property
    def target(self):
        return self._args[0]


#=========================================================================
_map_registery = {'map': Map, 'xmap': ProductMap, 'tmap': TensorMap}

_ = AnyArgument('_')
