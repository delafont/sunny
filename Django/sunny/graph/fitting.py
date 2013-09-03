
import rpy2.robjects as ro
from rpy2.robjects.numpy2ri import numpy2ri
from rpy2.robjects.packages import importr
from rpy2.rinterface import RRuntimeError
from numpy import asarray, round as nround, reshape
from math import log10

drc = importr('drc')

def list2r(L):
    """Transform a Python list into a string in R format: [1,2,'C'] -> "c(1,2,'C')" ."""
    if not isinstance(L,(list,tuple)): L = [L] # everything is a vector in R
    LL = ["'%s'"%v if isinstance(v,basestring) else str(v) for v in L] # add quotes if elements are strings
    return "c(%s)" % ','.join(LL)

def create_bins(min_x,max_x,nbins=100):
    inc = float(log10(max_x)-log10(min_x))/nbins
    intervals = [log10(min_x)+k*inc for k in range(nbins+1)]
    intervals = [10**x for x in intervals]
    return intervals

def normalize_response(response,model,fit_name):
    import_normalize()
    constraints = ro.r('constraints')
    param = constraints(model, fit_name)
    norm_response = response/(param.rx2('norm')[0]/100.)
    return norm_response

def fit_drm(data, fit_name='LL.4', norm=True):
    """:param data: a list of couples (dose,response)"""
    def model_drm(fit_name,dose,response):
        ro.r.assign('dose',numpy2ri(dose))
        ro.r.assign('response',numpy2ri(response))
        fit_fct = ro.r(fit_name+'()')
        try:
            model = drc.drm(ro.Formula('response~dose'),fct=fit_fct)
            return model
        except RRuntimeError, re:
            return "R: "+str(re)
    R_output = ""
    data = asarray(zip(*data))
    dose = data[0]; response = data[1]
    model = model_drm(fit_name,dose,response)
    if isinstance(model,basestring): # error string
        return None, data, R_output
    if norm:
        norm_response = normalize_response(response,model,fit_name)
        norm_data = zip(dose,nround(norm_response,2))
        # Re-fit normalized data
        model = model_drm(fit_name,dose,norm_response)
        if isinstance(model,basestring):
            return None, norm_data, R_output
        return model, norm_data, R_output
    else:
        return model, data, R_output

def compute_fitting_curve(model, interpolate=range(0,10000,10)):
    curve = model.rx2('curve')[0](ro.FloatVector(interpolate))
    curve = zip(interpolate,list(curve))
    return curve

def calculate_BMC(data, fit_name='LL.4', norm=True):
    model,norm_data,R_output = fit_drm(data, fit_name, norm)
    if model:
        BMC = ro.r('ED')(model,ro.IntVector([10,15]),interval=ro.StrVector(["delta"]),\
                         level=0.90,type="relative",display=False)
        BMC = ro.r('round')(BMC,4)
        BMC = reshape(asarray(BMC.rx(ro.IntVector([1,2,5,6,7,8]))), (3,-1)).T
        # BMC : [[Estimate1,Lower1,Upper1],[Estimate2,Lower2,Upper2]]
        BMC = {'10':list(BMC[0]), '15':list(BMC[1])}
        return BMC
    else:
        return R_output

def model_selection(data):
    import_model_selection()
    data = [(x.dose,x.response,x.experiment) for v in data.values() for x in v]
    dose,response,experiment = asarray(zip(*data))
    ro.r.assign('dose',numpy2ri(dose))
    ro.r.assign('response',numpy2ri(response))
    ro.r.assign('experiment',numpy2ri(experiment))
    bmdrcdata = ro.r('data.frame(dose=dose,response=response,experiment=experiment)')
    selected_model = ro.r('bestModel')(bmdrcdata)[0]
    return selected_model


################################ R SHIT #######################################


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

def import_model_selection():
    """ """
    # bmdrcdata: data.frame from original file, with at least dose and response columns
    ro.r("""
    bestModel <- function(bmdrcdata) {
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
            best <- mselect(modell, fctList=modelList)
            mynames <- rownames(best)
        }
        return(mynames)
    }""")

    ro.r("""
    nulldev <- function() {
        os <- Sys.info()['sysname']
        if (os=="Linux") {
            n <- "/dev/null"
        }
        else if (os=="Windows") {
            n <- "NUL"
        } else {
            n <- "/dev/null"
        }
        return(n)
    }""")

    ro.r("""
    mydrm <- function(mydrcdata, fct) {
        if(length(grep('globaldrcdata', ls(.GlobalEnv)))==0) {
            .GlobalEnv$globaldrcdata <- list()
        }
        l <- length(.GlobalEnv$globaldrcdata)
        .GlobalEnv$globaldrcdata[l+1] <- list(mydrcdata)
        l <- length(.GlobalEnv$globaldrcdata)
        epdrm <- paste("drm(.GlobalEnv$globaldrcdata[[",  l,
                       "]]$response ~ .GlobalEnv$globaldrcdata[[",  l,
                       "]]$dose, fct=",  fct,
                       "())",  sep='')
        drc <- eval(parse(text=epdrm))
        return(drc)
    }

    cleanupDrcData <- function() {
        if (exists("globaldrcdata", envir=globalenv())) {
            rm("globaldrcdata", envir=globalenv())
        }
    }
    """)



# plot(fit, type="all", broken=FALSE, xlim=c(0, max(d$dose)), ylim=c(0,100), lty="dashed", lwd=1.3, cex.lab=1.2, cex.main=2, cex=2)
# points(d$dose, fitted(fit)[1:length(d$dose)], col='blue')
# fit$curve[[1]](seq(10000))

