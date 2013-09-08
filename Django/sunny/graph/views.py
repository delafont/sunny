
### Django stuff
from graph.models import Measurement, Sample
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.utils import simplejson
from django.core.servers.basehttp import FileWrapper
#from django.core.serializers import serialize

### Custom functions
from fitting import *


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

    points,curves,bounds,loglist,BMC = fit_etc(samples)

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

#def create_images(request):
#    """Create the 5 R plots and add them to Sample.images"""
#    sample_id = simplejson.loads(request.GET.keys()[0][0])
#    sample = Sample.objects.filter(id=sample_id)
#    "R stuff here"
#    sample.images = None
#    return HttpResponse(1)

def getfile(request,pk):
    sample = Sample.objects.get(id=pk)
    response = HttpResponse(FileWrapper(sample.textfile), content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename='+sample.name+'.txt'
    return response

def getimages(request,pk):
    sample = Sample.objects.get(id=pk)
    measurements = Measurement.objects.filter(sample=pk)
    measurements = [(x.dose,x.response,x.experiment) for x in measurements]
    sample.images = generate_images(measurements)
    response = HttpResponse(FileWrapper(sample.images), content_type='application/gzip')
    response['Content-Disposition'] = 'attachment; filename='+sample.name+'.gzip'
    return response


