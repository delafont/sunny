
### Django stuff
from graph.models import Measurement, Sample, User
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.utils import simplejson
from django.core.servers.basehttp import FileWrapper
from django.core.files import File
from django import forms
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.shortcuts import render, redirect

### Custom functions
from fitting import *

### Usual imports
import tarfile
import glob


################################### LOGIN #####################################


class LoginForm(forms.Form):
    email = forms.CharField(max_length=100, required=True)
    password = forms.CharField(max_length=100, required=True, widget=forms.PasswordInput)
    new_account_log = forms.CharField(widget=forms.HiddenInput(), required=False)
    new_account_pwd = forms.CharField(widget=forms.HiddenInput(), required=False)

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        authenticated = False
        if form.is_valid():
            info = form.cleaned_data
            users_found = User.objects.filter(name=info['email'])
            if users_found:  # Check password, if ok redirect
                for user in users_found:
                    if check_password(info['password'], user.password):
                        authenticated = True
                if authenticated:
                    request.session['user'] = info['email']
                    return redirect('/graph/')
                    #return render(request, 'graph/index.html', {'User':info['email']})
                else:
                    messages.error(request, "Wrong password")
                    return render(request, 'graph/login.html', {'login_form':form})
            if info.get('new_account_log'):  # Create a new account and redirect
                if check_password(info['password'], info['new_account_pwd']) \
                and info['email'] == info['new_account_log']:
                    User.objects.create(name=info['email'], password=make_password(info['password']))
                    request.session['user'] = info['email']
                    return redirect('/graph/')
                    #return render(request, 'graph/index.html', {'User':info['email']})
                else:
                    messages.error(request, "You must enter the same password as for the first time.")
                    return render(request, 'graph/login.html', {'login_form':form})
            else:  # Ask for creating a new account
                messages.warning(request, "User not found. \
                    Enter you password again to create a new account with this email.")
                content = request.POST.copy()
                content.update({'new_account_log': info['email'],
                                'new_account_pwd': make_password(info['password'])})
                new_form = LoginForm(content)
                return render(request, 'graph/login.html', {'login_form':new_form})
    else:
        form = LoginForm() # An empty form
    return render(request, 'graph/login.html', {'login_form':form})


#################################### MAIN #####################################


def index(request):
    """Render the app's page on load"""
    if request.session.get('user'):
        user = User.objects.get(name=request.session['user'])
    ### DEBUG MODE ###
    else:
        if len(User.objects.all()) == 0:
            user = User.objects.create(name='julien.delafontaine@epfl.ch',password=make_password('f0231763'))
        else:
            user = User.objects.all()[0]
        request.session['user'] = user.name
    ### / DEBUG MODE ###
    samples = Sample.objects.filter(user=user.id)
    return render(request, 'graph/index.html', {'samples':samples, 'user':user.name})


def json_response(request):
    """Return a JSON {
        'points': {sample.id: {experiment: [data]}},
        'curves': {sample.id: {experiment: [data]}},
        'samples': [{'id': sample.id, ...}],
        'bounds': {sample.id: [xmin,xmax,ymin,ymax]},
        'loglist': ["logstring1",...],
        'BMC': {sample.id: bmc},
        'anchors': {sample.id: anchor},
        'avgcurve': {sample.id: curve_pooled},
    }
    `samples` determines which data will be returned.
    """
    samples = []
    # POST: New data - file upload, "Update" button or similar
    if request.method == 'POST':
        newdata = simplejson.loads(request.body)
        user = User.objects.get(name=request.session['user'])
        samples = Sample.objects.filter(user=user.id).filter(id__in=newdata['samples'])
        # Replace measurements for the corresponding samples
        Measurement.objects.filter(user=user.id).filter(sample__in=newdata['measurements']).delete()
        for newid in newdata["measurements"]:
            for mes in newdata["measurements"][newid]:
                Measurement.objects.create(dose=mes[0], response=mes[1], \
                                           experiment=mes[2], sample=samples.get(id=newid), user=user)
    # GET: OnLoad - requesting existing samples
    elif request.method == 'GET':
        user = User.objects.get(name=request.session['user'])
        if request.GET:
            sample_ids = simplejson.loads(request.GET.keys()[0])
            samples = Sample.objects.filter(user=user.id).filter(id__in=sample_ids)
        else: # no sample exists/is specified: take the first in the DB
            samples = list(Sample.objects.filter(user=user.id)[:1])
            if not samples:
                "Create a DefaultSample"
    points,curves,bounds,loglist,BMC,anchors,curves_pooled = fit_etc(samples)
    # Export
    samples = dict((s.id,{'id':s.id, 'name':s.name, 'sha1':s.sha1}) for s in samples)
    data = {'points': points,
            'curves': curves,
            'samples': samples,
            'bounds': bounds,
            'loglist': loglist,
            'BMC': BMC,
            'anchors': anchors,
            'curves_pooled':curves_pooled,
           }
    return HttpResponse(simplejson.dumps(data), content_type="application/json")


def new_sample(request):
    """Check if the given sample is new. If it is, return a new instance."""
    newsample = simplejson.loads(request.body)
    # Check if the file already is in the database, whatever its name is
    user = User.objects.get(name=request.session['user'])
    found = Sample.objects.filter(user=user.id).filter(sha1=newsample['sha1'])
    if not found:
        newsample = Sample.objects.create(name=newsample['name'], sha1=newsample['sha1'], user=user)
        response = {'new':True, 'id':newsample.id, 'name':newsample.name}
    else:
        old = found[0]
        old.name = newsample['name']
        old.save()
        response = {'new':False, 'id':old.id, 'name':newsample['name']}
    return HttpResponse(simplejson.dumps(response), content_type="application/json") # new sample

def remove_sample(request):
    sample_id = request.body
    Sample.objects.get(id=sample_id).delete()
    Measurement.objects.filter(sample=sample_id).delete()
    return HttpResponse(None)

def clear_all_db(request):
    user = User.objects.get(name=request.session['user'])
    Measurement.objects.filter(user=user.id).delete()
    Sample.objects.filter(user=user.id).delete()
    return index(request)

def getfile(request,pk):
    sample = Sample.objects.get(id=pk)
    response = HttpResponse(FileWrapper(sample.textfile), content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename='+sample.name+'.txt'
    return response

def getimages(request,pk):
    sample = Sample.objects.get(id=pk)
    measurements = Measurement.objects.filter(sample=pk)
    measurements = [(x.dose,x.response,x.experiment) for x in measurements]
    template = "sunny/media/images/fit_images_%s" % pk
    generate_images(measurements,template+'.png')
    with tarfile.open(template+".tar.gz", "w:gz") as tar:
        for filename in glob.glob(template+'*.png'):
            tar.add(filename,arcname=os.path.basename(filename),recursive=False)
            os.remove(filename)
    sample.images.save('5images_%s.tar.gz'%pk, File(open(template+".tar.gz")),save=True)
    os.remove(template+'.tar.gz')
    response = HttpResponse(FileWrapper(sample.images), content_type='application/gzip')
    response['Content-Disposition'] = 'attachment; filename=5images_%s.tar.gz' % pk
    return response


#------------------------------------------------------#
# This code was written by Julien Delafontaine         #
# Bioinformatics and Biostatistics Core Facility, EPFL #
# http://bbcf.epfl.ch/                                 #
# webmaster.bbcf@epfl.ch                               #
#------------------------------------------------------#
