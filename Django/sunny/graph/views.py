### Standard imports
import os, sys
import itertools

### Django stuff
from graph.models import Measurement, Sample
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import simplejson
#from django.core.serializers import serialize

### Custom functions
from fitting import *
#from util import sha1


def index(request):
    """Render the main page on load"""
    samples = Sample.objects.all()
    template = loader.get_template('graph/index.html')
    context = RequestContext(request, {
            'samples': samples,
        })
    return HttpResponse(template.render(context))


def json_response(request):
    """Return a JSON {
        'points': {sample.id: {experiment: [data]}},
        'curves': {sample.id: {experiment: [data]}},
        'samples': [{'id': sample.id, ...}],
        'bounds': {sample.id: [xmin,xmax,ymin,ymax]},
        'loglist': ["logstring1",...],
        'BMC': {sample.id: bmc},
    }
    `samples` determines which data will be returned.
    """
    samples = []

    # POST: New data - file upload, "Update" button or similar
    if request.method == 'POST':
        newdata = simplejson.loads(request.body)
        samples = Sample.objects.filter(id__in=newdata['samples'])
        # Replace measurements for the corresponding samples
        Measurement.objects.filter(sample__in=newdata['measurements']).delete()
        for newid in newdata["measurements"]:
            for mes in newdata["measurements"][newid]:
                Measurement.objects.create(dose=mes[0], response=mes[1], \
                                           experiment=mes[2], sample=samples.get(id=newid))
    # GET: OnLoad - requesting existing samples
    elif request.method == 'GET':
        if request.GET:
            sample_ids = simplejson.loads(request.GET.keys()[0])
            samples = Sample.objects.filter(id__in=sample_ids)
        else: # no sample exists/is specified: take the first in the DB
            samples = list(Sample.objects.all()[:1])
            if not samples:
                "Create a DefaultSample"

    points={}; curves={}; models={}; BMC={}; bounds={}
    loglist=[]; log=''; nbins=100
    xmin = ymin = sys.maxint
    xmax = ymax = -sys.maxint
    if samples:
        # Pool samples, select the best model and apply it to all together
        for s in samples:
            print '>>> Sample',s.name
            points[s.id]={}; curves[s.id]={}; bounds[s.id]=[xmin,xmax,ymin,ymax]
            measurements = Measurement.objects.filter(sample=s.id).order_by('experiment')
            measurements = dict((exp,list(mes)) for exp,mes in itertools.groupby(measurements,lambda x:x.experiment))
            measurements_pooled = [(x.dose,x.response,x.experiment) for exp in measurements for x in measurements[exp]]
            fit_name = model_selection(measurements_pooled)
            # Calculate the anchor point in case it will be needed
            if fit_name:
                anchor = calculate_anchor(measurements_pooled,fit_name)
                loglist.append('Model selected for sample %s: %s.' % (s.name,fit_name))
            else:
                loglist.append('No model found for sample %s.' % (s.name))
            # Apply best model to individual datasets
            for exp,pts in measurements.iteritems():
                print '>>> Experiment',exp
                pts = [(x.dose,x.response,x.experiment) for x in pts]
                if fit_name:
                    # Look if there is data < 5%, else add anchor point
                    below5 = [p for p in pts if p[1]<5]
                    if len(below5) == 0:
                        anchor_mes = Measurement.objects.create(dose=anchor[0], response=anchor[1], experiment=exp, sample=s)
                        measurements[exp].append(anchor_mes)
                        pts.append((anchor[0],anchor[1],exp))
                    model,pts,log = fit_drm(pts, fit_name, normalize=True)
                    models[exp] = model
                    loglist.append(log)
                    #print 'convergence',model.rx2(2).rx2('convergence')
                bounds = update_bounds(pts,bounds,s.id)
                points[s.id][exp] = pts
            # Compute the curves
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
            points_pooled = [p for exp,pts in points[s.id].iteritems() for p in pts]
            bmc = calculate_BMC(points_pooled, fit_name) if fit_name else ''
            if isinstance(bmc,basestring): # error string
                loglist.append("BMC not found for sample %s." % s.name)
                loglist.append(bmc)
                BMC[s.id] = []
            else:
                BMC[s.id] = bmc.get('15')
            # Export normalized data to text file
            if not (s.textfile and default_storage.exists(os.path.join(os.path.dirname(s.textfile.path),s.sha1)) ):
                file_content = '\t'.join(['dose','response','experiment'])+'\n'
                for p in points_pooled:
                    file_content += '\t'.join(['%s'%x for x in p])+'\n'
                file_content = ContentFile(file_content)
                s.textfile.save(s.sha1,file_content)

    # Export
    samples = dict((s.id,{'id':s.id, 'name':s.name, 'sha1':s.sha1}) for s in samples)
    data = {'points': points,
            'curves': curves,
            'samples': samples,
            'bounds': bounds,
            'loglist': loglist,
            'BMC': BMC,
           }
    return HttpResponse(simplejson.dumps(data), content_type="application/json")


def new_sample(request):
    """Check if the given sample is new. If it is, return a new instance."""
    newsample = simplejson.loads(request.body)
    # Check if the file already is in the database, whatever its name is
    found = Sample.objects.filter(sha1=newsample['sha1'])
    if not found:
        newsample = Sample(name=newsample['name'], sha1=newsample['sha1'])
        newsample.save()
        response = {'new':True, 'id':newsample.id, 'name':newsample.name}
    else:
        old = found[0]
        old.name = newsample['name']
        old.save()
        response = {'new':False, 'id':old.id, 'name':newsample['name']}
    return HttpResponse(simplejson.dumps(response), content_type="application/json") # new sample


def clear_all_db(request):
    Measurement.objects.all().delete()
    Sample.objects.all().delete()
    return index(request)
