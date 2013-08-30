from django.http import HttpResponse
from django.template import RequestContext, loader
from django.core.serializers import serialize
from django.utils import simplejson
from util import sha1
from fitting import fit_drm
from math import log10
import os
import itertools

from graph.models import Measurement, Sample

def _create_test_data():
    sam1 = Sample(name="MyTestSample")
    sam1.save()
    #mes3 = Measurement(dose=11,response=17,sample=sam1)
    #mes3.save()
    #measure_list = ["%s\n"%m for m in Measurement.objects.all()]
    #for filename in os.path.listdir("/Users/delafont/Dropbox/Workspace/Sunniva/input"):
    filename = "../../data/BIBF_k.txt"
    with open(filename) as f:
        f.readline()
        for line in f:
            sample_name = os.path.basename(os.path.splitext(filename)[0])
            dose,response,experiment = line.strip().split('\t')
            mes = Measurement(dose=float(dose),response=float(response), \
                              sample=sam1,experiment=int(experiment))
            mes.save()

def index(request):
    #_create_test_data()
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
        'fitted': {sample.id: {experiment: [data]}},
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
    # Upon changing sample (radio buttons)
    elif request.method == 'GET' and request.GET:
        sample_ids = simplejson.loads(request.GET.keys()[0])
        samples = Sample.objects.filter(id__in=sample_ids)

    # OnLoad, take the first
    elif request.method == 'GET':
        samples = list(Sample.objects.all()[:1])
        if not samples:
            "Create a DefaultSample"

    # Compute the curves and normalize the data points
    points = {}; curves = {}; fitteds = {}; loglist = []
    xmin = xmax = ymin = ymax = 0
    if samples:
        measurements = {}
        for s in samples:
            points[s.id]={}; curves[s.id]={}; fitteds[s.id]={}
            measurements = Measurement.objects.filter(sample=s.id).order_by('experiment')
            # Group by experiment
            measurements = dict((key,list(vals)) for key,vals in itertools.groupby(measurements,lambda x:x.experiment))
            for exp,pts in measurements.iteritems():
                pts = [(x.dose,x.response) for x in pts]
                min_x = min(x[0] for x in pts)
                max_x = max(x[0] for x in pts)
                min_y = min(0,min(x[1] for x in pts))
                max_y = max(100,max(x[1] for x in pts))
                nbins = 100
                inc = float(log10(max_x)-log10(min_x))/nbins
                intervals = [log10(min_x)+k*inc for k in range(nbins+1)]
                intervals = [10**x for x in intervals]
                norm_pts,curve,fitted,log = fit_drm(pts, interpolate=intervals, norm=True)
                points[s.id][exp] = norm_pts
                curves[s.id][exp] = curve
                #fitteds[s.id][exp] = fitted
                if len(curve) == 0: loglist.append("Failed to fit the model.")
                loglist.append(log)
                xmin = min(xmin,min_x)
                xmax = max(xmax,max_x)
                ymin = min(ymin,min_y)
                ymax = max(ymax,max_y)
        samples = dict((s.id,{'id':s.id, 'name':s.name, 'sha1':s.sha1}) for s in samples)
    else:
        points = {}#{-1: {-1:[]} }
        curves = {}#{-1: {-1:[]} }
        #fitteds = {}#{-1: {-1:[]} }
        loglist.append('No points to fit.')
        samples = {}#{-1:{'id':-1, 'name':''}}

    # Export
    data = {'points': points,
            'curves': curves,
            #'fitted': fitteds,
            'samples': samples,
            'bounds': [xmin,xmax,ymin,ymax],
            'loglist': loglist,
           }
    return HttpResponse(simplejson.dumps(data), content_type="application/json")


def new_sample(request):
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
