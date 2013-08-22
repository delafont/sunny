
import rpy2.robjects as ro
from rpy2.robjects.numpy2ri import numpy2ri
from rpy2.robjects.packages import importr
from rpy2.rinterface import RRuntimeError
from numpy import asarray


def list2r(L):
    """Transform a Python list into a string in R format: [1,2,'C'] -> "c(1,2,'C')" ."""
    if not isinstance(L,(list,tuple)): L = [L] # everything is a vector in R
    LL = ["'%s'"%v if isinstance(v,basestring) else str(v) for v in L] # add quotes if elements are strings
    return "c(%s)" % ','.join(LL)

def fit_drm(data,interpolate=range(0,10000,10)):
    """:param data: a list of couples (dose,response)"""
    dose,response = asarray(zip(*data))
    drc = importr('drc')
    fitted = ro.r('fitted')
    ro.r.assign('dose',numpy2ri(dose))
    ro.r.assign('response',numpy2ri(response))
    try:
        fit = drc.drm(ro.Formula('response~dose'),fct=ro.r('LL.4()'))
    except RRuntimeError, re:
        print re
        return [],[]
    curve = fit.rx2('curve')[0](ro.FloatVector(interpolate))
    curve = zip(interpolate,list(curve))
    fitted_points = zip(dose[:len(set(dose))], fitted(fit)[:len(set(dose))])
    return curve,fitted_points

###############################################################################

def test():
    import os
    data = []
    filename = "../../data/BIBF_k.txt"
    with open(filename) as f:
        f.readline()
        for line in f:
            sample_name = os.path.basename(os.path.splitext(filename)[0])
            dose,response,experiment = line.strip().split('\t')
            data.append((float(dose),float(response)))
    fit_drm(data)

if 0:
    test()


# plot(fit, type="all", broken=FALSE, xlim=c(0, max(d$dose)), ylim=c(0,100), lty="dashed", lwd=1.3, cex.lab=1.2, cex.main=2, cex=2)
# points(d$dose, fitted(fit)[1:length(d$dose)], col='blue')
# fit$curve[[1]](seq(10000))

