import numpy as np
def brentq(f,a,b,xtol=1e-10,maxiter=200):
    fa,fb=f(a),f(b)
    if fa*fb>0: raise ValueError('no sign change')
    for _ in range(maxiter):
        m=0.5*(a+b); fm=f(m)
        if abs(b-a)<xtol or fm==0: return m
        if fa*fm<0: b,fb=m,fm
        else: a,fa=m,fm
    return 0.5*(a+b)
class LinearConstraint:
    def __init__(s,*a,**k): pass
class Bounds:
    def __init__(s,*a,**k): pass
def milp(*a,**k): raise NotImplementedError
