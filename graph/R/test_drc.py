import rpy2.robjects as ro
from rpy2.robjects.numpy2ri import numpy2ri
from rpy2.robjects.packages import importr
from rpy2.rinterface import RRuntimeError
from numpy import asarray

drc = importr('drc')
ro.r("""source("functions.R")""")


def list2r(L):
    """Transform a Python list into a string in R format: [1,2,'C'] -> "c(1,2,'C')" ."""
    if not isinstance(L,(list,tuple)): L = [L] # everything is a vector in R
    LL = []
    for v in L:
        if isinstance(v,basestring): LL.append("'%s'"%v)
        elif v is None: LL.append('NA')
        else: LL.append(str(v))
    return "c(%s)" % ','.join(LL)

def get_params(model):
    params = list(model.rx2(2).rx2('par'))
    return params

def summary(model):
    info = {}
    info['fit_fct'] = model.rx2('fct').rx2('name')[0]
    info['param_names'] = list(model.rx2('fct').rx2('names'))
    info['coeffs'] = list(model.rx2('coefficients'))
    info['fixed'] = list(model.rx2('fct').rx2('fixed'))
    return info


param_names = {
               'LL.2': ['b','e'],
               'LL.3': ['b','d','e'],
               'LL.4': ['b','c','d','e'],
               'LL.5': ['b','c','d','e','f'],
               'W1.2': ['b','e'],
               'W1.3': ['b','d','e'],
               'W1.4': ['b','c','d','e'],
               'W2.4': ['b','c','d','e'],
              }
param_fixed = {
               'LL.2': {},
               'LL.3': {},
               'LL.4': {'c':0},
               'LL.5': {'c':0},
               'W1.2': {},
               'W1.3': {},
               'W1.4': {'c':0},
               'W2.4': {'c':0},
              }

#with open("../../sample_data/BIBF_k.txt") as f:
with open("../../sample_data/Geldanamycin_k.txt") as f:
    header = f.readline()
    data = [[int(line.split()[0]),float(line.split()[1])] for line in f]
    dose, response = zip(*data)

ro.r.assign('dose',numpy2ri(asarray(dose)))
ro.r.assign('response',numpy2ri(asarray(response)))


#fit_name = "LL.4"
fit_name = "W2.4"
fit_fct = ro.r(fit_name+'()')
#fixed = 'fixed='+list2r([0 if x in param_fixed[fit_name] else None for x in param_names[fit_name]])
#fit_fct = ro.r(fit_name+'('+fixed+')')

model = drc.drm(ro.Formula('response~dose'),fct=fit_fct)

# R list - index shifted by one
# [0]: NULL
# [1]: "fit": $par, $value, $convergence, $message, $hessian, $ovalue
# [2]: curve()
# ...
# [5]: ["b","c","d","e"]
# [6]: [[predicted values],[residuals]]
# [7]: call
# ...
# [9]: [parameters]
# ...
# [27]: same as [1][0] and 9: parameters
