from django.http import HttpResponse
from django.template import RequestContext, loader
from django.core.serializers import serialize
from django.utils import simplejson
from util import sha1
from fitting import fit_drm
from math import log10
import os

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
    measurements = Measurement.objects.all()
    template = loader.get_template('graph/index.html')
    context = RequestContext(request, {
            'samples': samples,
            'measurements': measurements,
        })
    return HttpResponse(template.render(context))

def json_response(request):
    if request.method == 'POST': # "Update" button or similar
        newdata = simplejson.loads(request.body)
        if newdata["sample"]:
            newid = newdata["sample"]["id"]
            Measurement.objects.filter(sample=newid).delete()
            sample = Sample.objects.filter(id=newid)[0]
            for mes in newdata["measurements"]:
                Measurement.objects.create(dose=mes[0], response=mes[1], experiment=mes[2], sample=sample)
    elif request.method == 'GET': # Upon changing sample (radio buttons)
        if request.GET:
            sample_id = request.GET['id']
            if sample_id == -1: # "All" radio button
                sample = Sample.objects.all()
            else: # other radio button
                sample = Sample.objects.filter(id=sample_id)[0]
        else: # OnLoad, take the first
            sample = list(Sample.objects.all()[:1])
            if sample: sample = sample[0]

    if sample:
        points = [(m.dose,round(m.response,2),m.experiment) for m in Measurement.objects.filter(sample=sample.id)]
        sample = {'id':sample.id, 'name':sample.name, 'sha1':sample.sha1}
    else:
        points = []
        sample = {'name':''}
    loglist = []

    if points:
        min_x = min(x[0] for x in points)
        max_x = max(x[0] for x in points)
        min_y = min(x[1] for x in points)
        max_y = max(x[1] for x in points)
        nbins = 100
        inc = float(log10(max_x)-log10(min_x))/nbins
        intervals = [log10(min_x)+k*inc for k in range(nbins+1)]
        intervals = [10**x for x in intervals]
        points,curve,fitted,log = fit_drm(points, interpolate=intervals, norm=True)
        experiment = m.experiment
    else:
        min_x = max_x = min_y = max_y = 0
        curve = []
        fitted = []
        experiment = ''
        log = 'No points to fit.\n'
    loglist.append(log)
    if len(curve) == 0:
        loglist.append("Failed to fit the model.")
    data = {'measurements': points,
            'sample': sample,
            'experiment': experiment,
            'curve': curve,
            'fitted': fitted,
            'bounds': [min_x,max_x,min_y,max_y],
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
