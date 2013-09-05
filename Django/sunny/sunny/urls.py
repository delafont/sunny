from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


def getfile(request,pk):
    from graph.models import Sample
    from django.http import HttpResponse
    from django.core.servers.basehttp import FileWrapper
    sample = Sample.objects.get(id=pk)
    response = HttpResponse(FileWrapper(sample.textfile), content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename='+sample.name+'.txt'
    return response


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sunny.views.home', name='home'),
    # url(r'^sunny/', include('sunny.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^graph/', include('graph.urls', namespace='graph')),
    url(r'^getfile/(?P<pk>\d+)', getfile, name='getfile'),
)
