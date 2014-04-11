
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
from numpy import asarray, round as nround, reshape, isnan
from math import log10
import os,sys,itertools


################################ MAIN CALL ####################################


def fit_etc(samples):
    points={}; curves={}; models={}; BMC={}; bounds={}; anchors={}; coeffs={}
    loglist=[]; log=''; nbins=100
    xmin = ymin = sys.maxint
    xmax = ymax = -sys.maxint
    if samples:

        # Pool samples, select the best model and apply it to all together
        for s in samples:
            print '>>> Sample', s
            points[s.id]={}; curves[s.id]={}; bounds[s.id]=[xmin,xmax,ymin,ymax]; coeffs[s.id]={}; BMC[s.id]={}
            measurements = Measurement.objects.filter(sample=s.id).order_by('experiment')
            measurements = dict((exp,list(mes)) for exp,mes in itertools.groupby(measurements,lambda x:x.experiment))
            measurements_pooled = [(x.dose,x.response,x.experiment) for exp in measurements for x in measurements[exp]]
            if len(measurements_pooled) == 0:
                continue # !!!
            print "* Model selection"
            fit_name = model_selection(measurements_pooled)

            # Calculate the anchor point in case it will be needed
            if fit_name:
                print "* Calculate anchor"
                anchor = calculate_anchor(measurements_pooled,fit_name)
                loglist.append('Model selected for sample %s: %s.' % (s.name,fit_name))
                print '.. Anchor:', anchor
                print "* Fit pooled data"
                model_pooled,pts_pooled,log_pooled = fit_drm(measurements_pooled, fit_name, normalize=True)
                if model_pooled:
                    minx_pooled = min(x[0] for x in measurements_pooled)
                    maxx_pooled = max(x[0] for x in measurements_pooled)
                    intervals_pooled = create_bins(minx_pooled,maxx_pooled,nbins)
                    curve_pooled = compute_fitting_curve(model_pooled, interpolate=intervals_pooled)
                    coeffs[s.id]['pooled'] = get_coeffs(model_pooled)
                    loglist.append('Model parameters: %s' % format_coeffs(coeffs[s.id]['pooled']))
                else:
                    curve_pooled = []
                curves[s.id]['pooled'] = curve_pooled
            else:
                loglist.append('No model found for sample %s.' % (s.name))

            # Apply best model to individual datasets
            print '* Fit individual datasets'
            for exp,pts in measurements.iteritems():
                pts = [(x.dose,x.response,x.experiment) for x in pts]
                if fit_name:
                    # Look if there is data < 5%, else add anchor point
                    below5 = [p for p in pts if p[1]<5]
                    if len(below5) == 0:
                        loglist.append('Anchor added to sample %s, exp. %s: (%.2f,%.2f)' \
                                        % (s.name, exp, anchor[0], anchor[1]))
                        anchors[s.id] = anchor
                        pts.append((anchor[0],anchor[1],exp))
                    print ".. Experiment %d" % exp
                    model,pts,log = fit_drm(pts, fit_name, normalize=True)
                    if model:
                        models[exp] = model
                        coeffs[s.id][exp] = get_coeffs(model)
                        loglist.append(log)
                            #print "Model:", model.rx2(2).rx2('par')
                            #print 'convergence',model.rx2(2).rx2('convergence')
                bounds = update_bounds(pts,bounds,s.id)
                points[s.id][exp] = pts

            # Compute the curves
            print "* Compute curves"
            intervals = create_bins(bounds[s.id][0],bounds[s.id][1],nbins)
            for exp,model in models.iteritems():
                if model:
                    models[exp] = model
                    curve = compute_fitting_curve(model, interpolate=intervals)
                else:
                    curve = []
                if len(curve) == 0: loglist.append("Failed to fit the model.")
                curves[s.id][exp] = curve

            # Calculate the BMC
            print "* Calculate BMC"
            points_pooled = [p for exp,pts in points[s.id].iteritems() for p in pts]
            bmc = calculate_BMC(points_pooled, fit_name) if fit_name else ''
            if isinstance(bmc,basestring): # error string
                loglist.append("BMC not found for sample %s." % s.name)
                loglist.append(bmc)
                BMC[s.id] = {'10':[0,0,0],'15':[0,0,0],'50':[0,0,0]}
            else:
                BMC[s.id] = bmc

            # Export normalized data to text file
            if not (s.textfile and default_storage.exists(os.path.join(os.path.dirname(s.textfile.path),s.sha1)) ):
                file_content = '\t'.join(['dose','response','experiment'])+'\n'
                for p in points_pooled:
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
    info = {'model': model}
    info['fit_name'] = model.rx2('fct').rx2('name')[0]
    info['names'] = list(model.rx2('fct').rx2('names'))
    info['coeffs'] = list(model.rx2('coefficients'))
    #info['fixed'] = list(model.rx2('fct').rx2('fixed'))
    return info

def get_coeffs(model):
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

def fit_drm(data, fit_name, normalize=True):
    """:param data: a list of couples (dose,response,experiment)"""
    def model_drm(fit_name,dose,response,fixed=''):
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
    def normalize_response(response,model):
        summary = model_summary(model)
        names = summary['names']
        coeffs = summary['coeffs']
        if 'd' in names:
            norm = coeffs[names.index('d')]
        else: norm = 100
        norm_response = response/(norm/100.)
        return norm_response
    R_output = ""
    data_array = asarray(zip(*data))
    dose = data_array[0]; response = data_array[1]; experiment = data_array[2]
    model = model_drm(fit_name,dose,response)
    if isinstance(model,basestring): # error string
        R_output += model
        return None, data, R_output
    if normalize:
        norm_response = normalize_response(response,model)
        norm_data = zip(dose,nround(norm_response,2),experiment)
        # Re-fit normalized data
        fixed = [0 if x in param_fixed[fit_name] else None for x in param_names[fit_name]]
        model = model_drm(fit_name,dose,norm_response, fixed=fixed)
        if isinstance(model,basestring):
            R_output += model
            return None, norm_data, R_output
        return model, norm_data, R_output
    else:
        return model, data, R_output


def format_coeffs(coeffs):
    out = ''
    for c in coeffs:
        out += '%s=%.2f, ' % c
    out.strip(' ,')
    return out

def compute_fitting_curve(model, interpolate=range(0,10000,10)):
    curve = model.rx2('curve')[0](ro.FloatVector(interpolate))
    curve = zip(interpolate,list(curve))
    return curve

def calculate_BMC(data, fit_name, normalize=True):
    """:param data: list of tuples (dose,response,experiment)"""
    model,norm_data,R_output = fit_drm(data, fit_name, normalize)
    if model:
        # R: EC(modell, [10,15,50], c("delta"), level=0.9, type="relative", display=FALSE)
        BMC = ro.r('ED')(model,ro.IntVector([10,15,50]),interval=ro.StrVector(["delta"]),\
                         level=0.90,type="relative",display=False)
        BMC = ro.r('round')(BMC,4)
        BMC = reshape(asarray(BMC.rx(ro.IntVector([1,2,3, 7,8,9, 10,11,12]))), (3,-1)).T
        # BMC : [[Estimate1,Lower1,Upper1],[Estimate2,Lower2,Upper2],...]
        BMC10 = [round(x,4) if not isnan(x) else 0 for x in BMC[0]]
        BMC15 = [round(x,4) if not isnan(x) else 0 for x in BMC[1]]
        BMC50 = [round(x,4) if not isnan(x) else 0 for x in BMC[2]]
        BMC = {'10':BMC10, '15':BMC15, '50':BMC50}
        return BMC
    else:
        return R_output

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

def calculate_anchor(pooled_data,fit_name):
    """:param pooled_data: list of tuples (dose,response,experiment)"""
    ec50 = calculate_BMC(pooled_data, fit_name).get('50',[0])[0]
    xmax = max(m[0] for m in pooled_data)
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

def update_bounds(pts,bounds,sid):
    min_x = min(x[0] for x in pts)
    max_x = max(x[0] for x in pts)
    min_y = min(0,min(x[1] for x in pts))
    max_y = max(100,max(x[1] for x in pts))
    bounds[sid][0] = min(bounds[sid][0], min_x)
    bounds[sid][1] = max(bounds[sid][1], max_x)
    bounds[sid][2] = min(bounds[sid][2], min_y)
    bounds[sid][3] = max(bounds[sid][3], max_y)
    return bounds

def generate_images(data,template):
    """:param data: list of tuples (dose,response,experiment)"""
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
