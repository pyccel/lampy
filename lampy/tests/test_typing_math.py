# TODO
#g = lambda xs,ys,z: [[x + y*z for x in xs] for y in ys]
#g = lambda xs,y,z: [x + y*z for x in xs]

import numpy as np
import time

from pyccel.decorators import types, pure
from pyccel.ast.datatypes import NativeInteger, NativeReal, NativeComplex, NativeBool

from lampy.lambdify import _lambdify
from lampy import TypeVariable, TypeTuple, TypeList
from lampy import add, mul

#=========================================================
def test_map_sin_list(**settings):
    settings['semantic_only'] = True

    L = lambda xs: map(sin, xs)

    type_L = _lambdify( L, **settings )

    assert( isinstance( type_L, TypeList ) )

    parent = type_L.parent
    assert( isinstance( parent.dtype, NativeReal ) )
    assert( parent.rank == 0 )
    assert( parent.precision == 8 )
    assert( not parent.is_stack_array )

    print('DONE.')

#==============================================================================
# CLEAN UP SYMPY NAMESPACE
#==============================================================================

def teardown_module():
    from sympy import cache
    cache.clear_cache()

def teardown_function():
    from sympy import cache
    cache.clear_cache()

###########################################
#if __name__ == '__main__':
#    settings = {'semantic_only' : True}
#
#    test_map_sin_list(**settings)
