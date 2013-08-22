from django.http import HttpResponse
from django.template import RequestContext, loader
from django.utils import simplejson
from fitting import fit_drm
import os

from graph.models import Measurement

def _create_test_data():
    mes3 = Measurement(dose=11,response=17)
    mes3.save()
    #measure_list = ["%s\n"%m for m in Measurement.objects.all()]
    #for filename in os.path.listdir("/Users/delafont/Dropbox/Workspace/Sunniva/input"):
    filename = "/Users/delafont/Dropbox/Workspace/Sunniva/input/BIBF_k.txt"
    with open(filename) as f:
        f.readline()
        for line in f:
            sample_name = os.path.basename(os.path.splitext(filename)[0])
            dose,response,experiment = line.strip().split('\t')
            mes = Measurement(dose=float(dose),response=float(response), \
                              sample=sample_name,experiment=int(experiment))
            mes.save()

def index(request):
    measure_list = Measurement.objects.all()
    template = loader.get_template('graph/index.html')
    context = RequestContext(request, {
            'measurements': measure_list,
        })
    return HttpResponse(template.render(context))

def json_response(request):
    if request.method == 'POST':
        Measurement.objects.all().delete()
        newdata = simplejson.loads(request.body)
        for mes in newdata:
            mes = Measurement(dose=mes[0], response=mes[1])
            mes.save()
    points = [(m.dose,m.response) for m in Measurement.objects.all()]
    if points:
        min_x = min(x[0] for x in points)
        max_x = max(x[0] for x in points)
        nbins = 200
        inc = float(max_x-min_x)/nbins
        interval_range = [min_x+k*inc for k in range(nbins+1)]
        curve,fitted = fit_drm(points, interpolate=interval_range)
        sample = m.sample
        experiment = m.experiment
    else:
        min_x = max_x = 0
        curve = []
        fitted = []
        sample = ''
        experiment = ''
    measurements = {'measurements': points,
                    'sample': sample,
                    'experiment': experiment,
                    'curve': curve,
                    'fitted': fitted,
                    'bounds': [min_x,max_x],
                    'fitting_error': False
                   }
    if len(curve) == 0:
        measurements['fitting_error'] = True
    return HttpResponse(simplejson.dumps(measurements), content_type="application/json")

