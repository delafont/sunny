
import rpy2.robjects as ro
from rpy2.robjects.numpy2ri import numpy2ri
from rpy2.robjects.packages import importr
from rpy2.rinterface import RRuntimeError
from numpy import asarray, round as nround


def list2r(L):
    """Transform a Python list into a string in R format: [1,2,'C'] -> "c(1,2,'C')" ."""
    if not isinstance(L,(list,tuple)): L = [L] # everything is a vector in R
    LL = ["'%s'"%v if isinstance(v,basestring) else str(v) for v in L] # add quotes if elements are strings
    return "c(%s)" % ','.join(LL)

def fit_drm(data,interpolate=range(0,10000,10), norm=True):
    """:param data: a list of couples (dose,response)"""
    R_output = ""
    dose,response = asarray(zip(*data))
    drc = importr('drc')
    fitted = ro.r('fitted')
    ro.r.assign('dose',numpy2ri(dose))
    ro.r.assign('response',numpy2ri(response))
    fit_name = 'LL.4'
    fit_fct = ro.r(fit_name+'()')
    # Model selection
    bmdrcdata = ro.r('')
    linreg = ro.r('')
    mselect = ro.r('bestModel')
    selected_model = mselect(bmdrcdata,linreg)
    print selected_model
    # Apply the model
    try:
        model = drc.drm(ro.Formula('response~dose'),fct=fit_fct)
    except RRuntimeError, re:
        return data, [],[], "R: "+str(re)
    # Normalization
    import_normalize()
    constraints = ro.r('constraints')
    param = constraints(model, fit_name)
    norm_response = response/(param.rx2('norm')[0]/100.)
    ro.r.assign('response',numpy2ri(norm_response))
    try:
        model = drc.drm(ro.Formula('response~dose'),fct=fit_fct)
    except RRuntimeError, re:
        return data, [],[], "R: "+str(re)
    curve = model.rx2('curve')[0](ro.FloatVector(interpolate))
    curve = zip(interpolate,list(curve))
    fitted_points = zip(dose[:len(set(dose))], fitted(model)[:len(set(dose))])
    norm_data = zip(dose,nround(norm_response,2))
    return norm_data,curve,fitted_points,R_output

def import_normalize():
    """Extract one of the fitting parameters.
    `norm` is the scaling factor; ``..."""
    ro.r("""
        constraints <- function(objdrc, fctname){
            parameter <- matrix(coef(objdrc))
            switch(fctname,
               "LL.3" = {
                 norm<-parameter[2]
                 fixedP=c(NA, NA, NA)
                 KoefName=c("b=","d=", "e=")
                 AnzK=3
               }, "W1.4" = {
                 norm<-parameter[3]
                 fixedP=c(NA, 0, NA, NA)
                 KoefName=c("b=", "d=", "e=")
                 AnzK=3
               }, "W2.4" = {
                 norm<-parameter[3]
                 fixedP=c(NA, 0, NA, NA)
                 KoefName=c("b=", "d=", "e=")
                 AnzK=3
               }, "LL.4" = {
                 norm<-parameter[3]
                 fixedP=c(NA, 0, NA, NA)
                 KoefName=c("b=", "d=", "e=")
                 AnzK=3
               }, "LL.5" = {
                 norm<-parameter[3]
                 fixedP=c(NA, 0, NA, NA, NA)
                 KoefName=c("b=", "d=", "e=", "f=")
                 AnzK=4
            })
        return(list(norm=norm, fixedP=fixedP, KoefName=KoefName, AnzK=AnzK))
        } """)

def model_selection():
    """ """
    ro.r("""
    bestModel <- function(bmdrcdata, linreg) {
        modelList <- list(LL.4(), LL.5(), W1.4(), W2.4(), LL.3())
        modell <- NULL
        for(n in seq(length(modelList))) {
            curModelName <- modelList[[n]]$name
            trymodeltxt <- paste("mydrm(bmdrcdata, fct='", curModelName,"')", sep="")
            capture.output(modell <- try(eval(parse(text=trymodeltxt))), file=nulldev())
            if (!(class(modell)=="try-error")) { break(); }
        }
        if (class(modell)=="try-error") { # no model found
            mynames <- NULL
        } else {
            best <- mselect(modell, fctList=modelList, linreg=linreg)
            mynames <- rownames(best)
        }
        print(mynames)
        return(mynames)
    }
    """)

###############################################################################

def test():
    import os
    data = []
    filename = "../../data/BIBF_k.txt"
    with open(filename) as f:
        f.readline()
        for line in f:
            sample_name = os.path.basename(os.path.splitext(filename)[0])
            dose,response = line.strip().split('\t')
            data.append((float(dose),float(response)))
    fit_drm(data)

if 0:
    test()


# plot(fit, type="all", broken=FALSE, xlim=c(0, max(d$dose)), ylim=c(0,100), lty="dashed", lwd=1.3, cex.lab=1.2, cex.main=2, cex=2)
# points(d$dose, fitted(fit)[1:length(d$dose)], col='blue')
# fit$curve[[1]](seq(10000))

