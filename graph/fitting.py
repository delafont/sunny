
### Django stuff
from graph.models import Measurement
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

### rpy2
import rpy2.robjects as ro
from rpy2.robjects.numpy2ri import numpy2ri
from rpy2.robjects.packages import importr
from rpy2.rinterface import RRuntimeError

### Standard imports
from numpy import asarray, round as nround
import numpy
from math import log10
import os,sys,itertools


################################ MAIN CALL ####################################


def fit_etc(samples):
    points={}; curves={}; models={}; BMC={}; bounds={}; anchors={}; coeffs={}
    loglist=[]; log=''; nbins=100
    xmin = ymin = sys.maxint
    xmax = ymax = -sys.maxint
    if samples:
        for s in samples:
            print '>>> Sample', s
            points[s.id]={}; curves[s.id]={}; bounds[s.id]=[xmin,xmax,ymin,ymax]; coeffs[s.id]={}; BMC[s.id]={}
            measurements = Measurement.objects.filter(sample=s.id).order_by('experiment')
            data = dict((exp,list(mes)) for exp,mes in itertools.groupby(measurements,lambda x:x.experiment))

            # Pool experiments, select the best model
            dataP = [(x.dose,x.response,x.experiment) for x in measurements]
            if len(dataP) == 0:
                continue # !!!
            print "* Model selection"
            fit_name = model_selection(dataP)

            # Apply the model to the pooled data, norm, calculate the curve
            # Calculate the anchor point in case it will be needed
            if fit_name:
                loglist.append('Model selected for sample %s: %s.' % (s.name,fit_name))
                print "* Fit pooled data"
                # Fit a first time to get the norm parameter
                modelPN,dataPN,logPN = fit_drm(dataP, fit_name, normalize=True)
                if modelPN:
                    print "* Calculate anchor"
                    anchor = calculate_anchor(modelPN, dataPN)
                    print '.. Anchor:', anchor
                    # Calculate the curve for the pooled data
                    minxPN = min(x[0] for x in dataPN)
                    maxxPN = max(x[0] for x in dataPN)
                    intervalsPN = create_bins(minxPN,maxxPN,nbins)
                    curvePN = compute_fitting_curve(modelPN, intervalsPN)
                    coeffs[s.id]['pooled'] = get_coeffs(modelPN)
                    loglist.append('Model parameters: %s' % format_coeffs(coeffs[s.id]['pooled']))
                else:
                    curvePN = []
                    loglist.append(logPN)
                curves[s.id]['pooled'] = curvePN
            else:
                loglist.append('No model found for sample %s.' % (s.name))

            # Apply best model to individual datasets
            print '* Fit individual datasets'
            for exp,mes in data.iteritems():
                print ".. Experiment %d" % exp
                dataE = [(x.dose,x.response,x.experiment) for x in mes]
                if fit_name:
                    # Fit a first time to normalize
                    modelEN,dataEN,logEN = fit_drm(dataE, fit_name, normalize=True)
                    # Look if there is data < 5%, else add anchor point
                    below5 = [p for p in dataEN if p[1]<5]
                    if len(below5) == 0:
                        loglist.append('Anchor added to sample %s, exp. %s: (%.2f,%.2f)' \
                                        % (s.name, exp, anchor[0], anchor[1]))
                        anchors[s.id] = anchor
                        dataEN.append((anchor[0],anchor[1],exp))
                    # Fit again with the anchor added
                    modelEAN,dataEAN,logEAN = fit_drm(dataEN, fit_name, normalize=True)
                    if modelEAN:
                        models[exp] = modelEAN
                        coeffs[s.id][exp] = get_coeffs(modelEAN)
                        loglist.append(logEAN)
                else:
                    dataEAN = dataE
                bounds[s.id] = update_bounds(dataEAN,bounds[s.id])
                points[s.id][exp] = dataEAN

            # Compute the curves for the individual datasets
            print "* Compute individual curves"
            intervals = create_bins(bounds[s.id][0],bounds[s.id][1],nbins)
            for exp,model in models.iteritems():
                if model:
                    models[exp] = model
                    curve = compute_fitting_curve(model, intervals)
                else:
                    curve = []
                if len(curve) == 0:
                    loglist.append("Failed to fit the model.")
                curves[s.id][exp] = curve

            # Calculate the BMC
            # Pool the independantly normalized exp data with their anchor points
            print "* Calculate BMC"
            bmc = ''
            percents = [10,15,30,50]
            pointsP = [p for exp,pts in points[s.id].iteritems() for p in pts]
            if fit_name:
                modelPN,dataPN,logPN = fit_drm(pointsP, fit_name, normalize=True)
                if modelPN:
                    bmc = calculate_BMC(modelPN, percents)
                else:
                    bmc = ''
                    loglist.append(logPN)
            if isinstance(bmc,basestring): # error string
                loglist.append("BMC not found for sample %s." % s.name)
                loglist.append(bmc)
                BMC[s.id] = dict((p,[0,0,0]) for p in percents)
            else:
                BMC[s.id] = bmc

            # Export normalized data to text file
            if not (s.textfile and default_storage.exists(os.path.join(os.path.dirname(s.textfile.path),s.sha1)) ):
                file_content = '\t'.join(['dose','response','experiment'])+'\n'
                for p in pointsP:
                    file_content += '\t'.join(['%s'%x for x in p])+'\n'
                file_content = ContentFile(file_content)
                s.textfile.save(s.sha1,file_content)

    return points,curves,bounds,loglist,BMC,anchors,coeffs


################################## FITTING #####################################

def list2r(L):
    """Transform a Python list into a string in R format: [1,2,'C'] -> "c(1,2,'C')" ."""
    if not isinstance(L,(list,tuple)): L = [L] # everything is a vector in R
    LL = []
    for v in L:
        if isinstance(v,basestring): LL.append("'%s'"%v)
        elif v is None: LL.append('NA')
        else: LL.append(str(v))
    return "c(%s)" % ','.join(LL)

def model_summary(model):
    """Extract useful info from the R object *model*."""
    info = {'model': model}
    info['fit_name'] = model.rx2('fct').rx2('name')[0]
    info['names'] = list(model.rx2('fct').rx2('names'))
    info['coeffs'] = list(model.rx2('coefficients'))
    info['convergence'] = model.rx2(2).rx2('convergence')
    return info

def get_coeffs(model):
    """Return a dict {param_name: param_value} from the R object *model*."""
    summary = model_summary(model)
    return zip(summary['names'],summary['coeffs'])

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

def fit_drm(data, fit_name, fixed='', normalize=True):
    """:param data: a list of couples (dose,response,experiment)"""
    def model_drm(fit_name,dose,response,fixed):
        ro.r.assign('dose',numpy2ri(dose))
        ro.r.assign('response',numpy2ri(response))
        if fixed:
            fixed = 'fixed='+list2r(list(fixed))
        fit_fct = ro.r(fit_name+'('+fixed+')')
        try:
            model = drc.drm(ro.Formula('response~dose'),fct=fit_fct)
            return model
        except RRuntimeError, re:
            return "R: "+str(re)
    R_output = ""
    data_array = asarray(zip(*data))
    dose = data_array[0]; response = data_array[1]
    model = model_drm(fit_name,dose,response,fixed)
    if isinstance(model,basestring): # error string
        R_output += model
        return None, data, R_output
    else:
        if normalize:
            data = rescale(data,model)
            data_array = asarray(zip(*data))
            dose = data_array[0]; response = data_array[1]
            # Now fix c=0 for the fit (?)
            fixed = [0 if x in param_fixed[fit_name] else None for x in param_names[fit_name]]
            model = model_drm(fit_name,dose,response,fixed)
        return model, data, R_output

def rescale(data, model):
    """Divides all response values by the parameter "d" of the model (intercept),
    so that survival always starts at 100%."""
    data_array = asarray(zip(*data))
    dose = data_array[0]; response = data_array[1]; experiment = data_array[2]
    summary = model_summary(model)
    names = summary['names']
    coeffs = summary['coeffs']
    if 'd' in names:
        norm = coeffs[names.index('d')]
    else:
        norm = 100
    norm_response = response/(norm/100.)
    norm_data = zip(dose,nround(norm_response,2),experiment)
    return norm_data

def format_coeffs(coeffs):
    """From a list [(coeff_name,value), ...], return a string 'coeff_name=value, ...'
    to be printed in the log."""
    out = ''
    for c in coeffs:
        out += '%s=%.2f, ' % c
    out.strip(' ,')
    return out

def compute_fitting_curve(model, intervals=range(0,10000,10)):
    """Return a list of points (x,y) where y values are ordinates of the fitting curve
    corresponding to x values given in *intervals*."""
    curve = model.rx2('curve')[0](ro.FloatVector(intervals))
    curve = zip(intervals,list(curve))
    return curve

def calculate_BMC(model, percents=[10,15,30,50]):
    """Return a dict {BMR: (BMC,BMCL,BMCU)}."""
    # R: EC(modell, [10,15,50], c("delta"), level=0.9, type="relative", display=FALSE)
    BMC = ro.r('ED')(model,ro.IntVector(percents),interval=ro.StrVector(["delta"]),\
                     level=0.90,type="relative",display=False)
    BMC = asarray(ro.r('round')(BMC,4))
    BMC = numpy.delete(BMC, 1, 1)
    BMC = dict((p,[round(x,4) if not numpy.isnan(x) else 0 for x in BMC[i]]) for i,p in enumerate(percents))
    return BMC

def model_selection(data):
    """:param data: list of tuples (dose,response,experiment)"""
    dose,response,experiment = asarray(zip(*data))
    ro.r.assign('dose',numpy2ri(dose))
    ro.r.assign('response',numpy2ri(response))
    ro.r.assign('experiment',numpy2ri(experiment))
    bmdrcdata = ro.r('data.frame(dose=dose,response=response,experiment=experiment)')
    selected_models = ro.r('bestModel')(bmdrcdata)
    if selected_models == ro.rinterface.NULL: # No model found
        selected_model = None
    else:
        selected_model = selected_models[0]
    return selected_model

def calculate_anchor(model, data):
    """:param pooled_data: list of tuples (dose,response,experiment)"""
    ec50 = calculate_BMC(model).get('50',[0])[0]
    xmax = max(m[0] for m in data)
    if ec50:
        anchor = (min(100*ec50,100*xmax),0)
    else:
        anchor = (100*xmax,0)
    return anchor

def create_bins(min_x,max_x,nbins=100):
    if min_x == 0: min_x = 1e-10
    if max_x == 0: max_x = 1e-10
    inc = float(log10(max_x)-log10(min_x))/nbins
    intervals = [log10(min_x)+k*inc for k in range(nbins+1)]
    intervals = [10**x for x in intervals]
    return intervals

def update_bounds(pts,bounds):
    """Update the global min/max values to get the right x values to plot the curves."""
    min_x = min(x[0] for x in pts)
    max_x = max(x[0] for x in pts)
    min_y = min(0,min(x[1] for x in pts))
    max_y = max(100,max(x[1] for x in pts))
    bounds[0] = min(bounds[0], min_x)
    bounds[1] = max(bounds[1], max_x)
    bounds[2] = min(bounds[2], min_y)
    bounds[3] = max(bounds[3], max_y)
    return bounds

def generate_images(data,template):
    """Run Sunniva's R script to generate the 5 plots she likes.
    :param data: list of tuples (dose,response,experiment)"""
    ro.r("""
    source("graph/R/machPlots.R")
    source("graph/R/processData.R")
    """)
    data_array = asarray(zip(*data))
    dose = data_array[0]; response = data_array[1]; experiment = data_array[2]
    ro.r.assign('dose',numpy2ri(dose))
    ro.r.assign('response',numpy2ri(response))
    ro.r.assign('experiment',numpy2ri(experiment))
    ro.r.assign('outfilename',template)
    ro.r("""
    mydata = data.frame(dose=dose,response=response,experiment=experiment)
    processData(mydata, title="DRM", xlab="Dose", outfilename=outfilename, cooksfilename='', run=3)
    """)


########################### AUTO IMPORTS AT START #############################

# Auto import on app start
drc = importr('drc')
ro.r("""source("graph/R/functions.R")""")



#------------------------------------------------------#
# This code was written by Julien Delafontaine         #
# Bioinformatics and Biostatistics Core Facility, EPFL #
# http://bbcf.epfl.ch/                                 #
# webmaster.bbcf@epfl.ch                               #
#------------------------------------------------------#
