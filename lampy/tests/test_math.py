# TODO
#g = lambda xs,ys,z: [[x + y*z for x in xs] for y in ys]
#g = lambda xs,y,z: [x + y*z for x in xs]

import numpy as np
import time

from pyccel.decorators import types, pure

from lampy.lambdify import _lambdify


#=========================================================
def test_annotate_map_list(**settings):
    sin = np.sin
    l = lambda xs: map(sin, xs)
    L = _lambdify( l, **settings )
    xs = np.linspace(0., np.pi, 100)
    out = L(xs)
    expected = list(l(xs))

    assert(np.allclose( out, expected ))

    print('DONE.')

#==============================================================================
# CLEAN UP SYMPY NAMESPACE
#==============================================================================

def teardown_module():
#    from sympy import cache
    import sympy.core.cache as cache

    cache.clear_cache()

def teardown_function():
#    from sympy import cache
    import sympy.core.cache as cache
    cache.clear_cache()


##########################################
#if __name__ == '__main__':
#    settings = {}
##    settings = {'ast_only' : True}
##    settings = {'printing_only' : True}
#
#    test_annotate_map_list(**settings)
