# coding: utf-8

# TODO use pytest

from lampy.syntax import parse

L = parse('lambda x: 1')
L = parse('lambda xs: map(g, xs)')
L = parse('lambda xs,ys:  map(g, xs, ys)')
L = parse('lambda xs,ys:  xmap(g, xs, ys)')
L = parse('lambda xs,ys:  tmap(g, xs, ys)')
L = parse('lambda xs,ys:  reduce(add, map(f, xs, ys))')

# g is a function of 2 arguments => use abstract function
L = parse('lambda a,xs: map(lambda x: g(x,a), xs)')
L = parse('lambda a,xs: map(lambda _: g(a,_), xs)')
