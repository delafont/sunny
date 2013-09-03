from django.http import HttpResponse
from django.template import RequestContext, loader
from django.core.serializers import serialize
from django.utils import simplejson
from util import sha1
from fitting import *
import os
import itertools

from graph.models import Measurement, Sample


def index(request):
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
        'bounds': [xmin,xmax,ymin,ymax],
        'loglist': ["logstring1",...]
    }
    `samples` determines which data will be returned.
    """
    # "Update" button or similar
    if request.method == 'POST':
        newdata = simplejson.loads(request.body)
        samples = Sample.objects.filter(id__in=newdata['samples'])
        # Replace measurements for the corresponding samples
        Measurement.objects.filter(sample__in=newdata['measurements']).delete()
        for newid in newdata["measurements"]:
            for mes in newdata["measurements"][newid]:
                Measurement.objects.create(dose=mes[0], response=mes[1], \
                                           experiment=mes[2], sample=samples.get(id=newid))
    # OnLoad, or upon changing sample (radio buttons)
    elif request.method == 'GET':
        if request.GET:
            sample_ids = simplejson.loads(request.GET.keys()[0])
            samples = Sample.objects.filter(id__in=sample_ids)
        else: # no sample exists/is specified: take the first in the DB
            samples = list(Sample.objects.all()[:1])
            if not samples:
                "Create a DefaultSample"

    # Compute the curves and normalize the data points
    points={}; curves={}; loglist=[]; BMC={}
    xmin = xmax = ymin = ymax = 0
    nbins = 100
    if samples:
        measurements = {}
        for s in samples:
            norm_points = []
            points[s.id]={}; curves[s.id]={}
            measurements = Measurement.objects.filter(sample=s.id).order_by('experiment')
            # Group by experiment, select the best model and apply it to all together
            measurements = dict((exp,list(mes)) for exp,mes in itertools.groupby(measurements,lambda x:x.experiment))
            fit_name = model_selection(measurements)
            loglist.append('Model selected for sample %s: %s.' % (s.name,fit_name))
            # Compute the curves
            for exp,pts in measurements.iteritems():
                pts = [(x.dose,x.response) for x in pts]
                min_x = min(x[0] for x in pts)
                max_x = max(x[0] for x in pts)
                min_y = min(0,min(x[1] for x in pts))
                max_y = max(100,max(x[1] for x in pts))
                intervals = create_bins(min_x,max_x,nbins)
                # Model each experiment separately to get the curves
                model,norm_pts,log = fit_drm(pts, fit_name, norm=True)
                curve = compute_fitting_curve(model, interpolate=intervals)
                points[s.id][exp] = norm_pts
                curves[s.id][exp] = curve
                norm_points.extend(norm_pts)
                if len(curve) == 0: loglist.append("Failed to fit the model.")
                loglist.append(log)
                xmin = min(xmin,min_x)
                xmax = max(xmax,max_x)
                ymin = min(ymin,min_y)
                ymax = max(ymax,max_y)
            # Calculate the BMC
            bmc = calculate_BMC(norm_points, fit_name)
            if isinstance(bmc,basestring): # error string
                loglist.append('BMC not found for sample %s:' % s.name)
                loglist.append(bmc)
                BMC[s.id] = {}
            else:
                BMC[s.id] = BMC
        samples = dict((s.id,{'id':s.id, 'name':s.name, 'sha1':s.sha1}) for s in samples)
    else:
        samples = {}
        loglist.append('No points to fit.')

    # Export
    data = {'points': points,
            'curves': curves,
            'samples': samples,
            'bounds': [xmin,xmax,ymin,ymax],
            'loglist': loglist,
            'BMC': BMC.get('15'),
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
