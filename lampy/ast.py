# coding: utf-8

from sympy import Symbol

from pyccel.ast.basic import Basic

#=========================================================================
class BasicMap(Basic):
    """."""

    def __new__( cls, func, target ):

        return Basic.__new__(cls, func, target)

    @property
    def func(self):
        return self._args[0]

    @property
    def target(self):
        return self._args[1]

class Map(BasicMap):
    pass

class ProductMap(BasicMap):
    pass

class TensorMap(BasicMap):
    pass

#=========================================================================
class Zip(Basic):
    def __new__( cls, *args ):
        return Basic.__new__(cls, args)

    @property
    def arguments(self):
        return self._args[0]

    def __len__(self):
        return len(self.arguments)

#=========================================================================
class Product(Basic):
    def __new__( cls, *args ):
        return Basic.__new__(cls, args)

    @property
    def arguments(self):
        return self._args[0]

    def __len__(self):
        return len(self.arguments)

#=========================================================================
class Reduce(Basic):
    """."""

    def __new__( cls, func, target ):

        return Basic.__new__(cls, func, target)

    @property
    def func(self):
        return self._args[0]

    @property
    def target(self):
        return self._args[1]

#==========================================================================
# any argument
class AnyArgument(Symbol):
    pass


#=========================================================================
_map_registery = {'map': Map, 'xmap': ProductMap, 'tmap': TensorMap}

_ = AnyArgument('_')
