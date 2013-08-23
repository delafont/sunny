from django.http import HttpResponse
from django.template import RequestContext, loader
from django.core.serializers import serialize
from django.utils import simplejson
from fitting import fit_drm
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
    print Sample.objects.all()[0].id
    measure_list = Measurement.objects.all()
    template = loader.get_template('graph/index.html')
    context = RequestContext(request, {
            'measurements': measure_list,
        })
    return HttpResponse(template.render(context))

def json_response(request):
    if request.method == 'POST':
        sam = Sample.objects.all()[0]
        Measurement.objects.all().delete()
        newdata = simplejson.loads(request.body)
        for mes in newdata:
            mes = Measurement(dose=mes[0], response=mes[1], sample=sam)
            mes.save()
    points = [(m.dose,round(m.response,2)) for m in Measurement.objects.all()]
    loglist = []
    if points:
        min_x = min(x[0] for x in points)
        max_x = max(x[0] for x in points)
        min_y = min(x[1] for x in points)
        max_y = max(x[1] for x in points)
        nbins = 200
        inc = float(max_x-min_x)/nbins
        interval_range = [min_x+k*inc for k in range(nbins+1)]
        points,curve,fitted,log = fit_drm(points, interpolate=interval_range, norm=True)
        sample = m.sample.name
        experiment = m.experiment
    else:
        min_x = max_x = min_y = max_y = 0
        curve = []
        fitted = []
        sample = ''
        experiment = ''
        log = 'No points to fit.\n'
    loglist.append(log)
    measurements = {'measurements': points,
                    'sample': sample,
                    'experiment': experiment,
                    'curve': curve,
                    'fitted': fitted,
                    'bounds': [min_x,max_x,min_y,max_y],
                    'fitting_error': False,
                    'loglist': loglist,
                   }
    if len(curve) == 0:
        measurements['fitting_error'] = True
        measurements['loglist'] += ["Failed to fit the model."]
    return HttpResponse(simplejson.dumps(measurements), content_type="application/json")

