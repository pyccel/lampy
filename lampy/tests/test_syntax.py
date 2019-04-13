# coding: utf-8

# TODO use pytest

from lampy.syntax import parse

#=========================================================================
def test_syntax_1():
    L = parse('lambda x: 1')
    L = parse('lambda xs: map(g, xs)')
    L = parse('lambda xs,ys:  map(g, xs, ys)')
    L = parse('lambda xs,ys:  xmap(g, xs, ys)')
    L = parse('lambda xs,ys:  tmap(g, xs, ys)')
    L = parse('lambda xs,ys:  reduce(add, map(f, xs, ys))')

    # g is a function of 2 arguments => use abstract function
    L = parse('lambda a,xs: map(lambda x: g(x,a), xs)')
    L = parse('lambda a,xs: map(lambda _: g(a,_), xs)')

#=========================================================================
def test_syntax_partial_1():
    L = parse('lambda _,_: partial(f, x=_, y=_)')

#=========================================================================
# CLEAN UP SYMPY NAMESPACE
#=========================================================================

def teardown_module():
    from sympy import cache
    cache.clear_cache()

def teardown_function():
    from sympy import cache
    cache.clear_cache()

##########################################
#if __name__ == '__main__':
#    test_syntax_1()
#    test_syntax_partial_1()
