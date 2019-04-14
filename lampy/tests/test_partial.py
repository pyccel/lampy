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
@pure
@types('double')
def f1(x):
    r = x**2
    return r

@pure
@types('double', 'double')
def f2(x,y):
    r = x*y
    return r

#=========================================================
def test_lambda_1(**settings):
    l = lambda xs:  map(lambda _: f1(_), xs)

    L = _lambdify( l, namespace = {'f1': f1}, **settings )

    xs = range(0, 5)
    out = L(xs)
    expected = [0., 1, 4., 9., 16.]
    assert(np.allclose( out, expected ))

    print('DONE.')


##=========================================================
#def test_partial_1(**settings):
#    l = lambda xs,ys:  map(map(lambda _: partial(f2, x=_), xs), ys)
#
#    L = _lambdify( l, namespace = {'f2': f2}, **settings )
#
#    print('DONE.')


#=========================================================================
# CLEAN UP SYMPY NAMESPACE
#=========================================================================

def teardown_module():
    from sympy import cache
    cache.clear_cache()

def teardown_function():
    from sympy import cache
    cache.clear_cache()


#############################################
#if __name__ == '__main__':
#    settings = {}
##
##    test_lambda_1(**settings)
#    test_partial_1(**settings)
