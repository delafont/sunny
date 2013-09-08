from django.conf.urls import patterns, include, url
from graph.views import getfile, getimages

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sunny.views.home', name='home'),
    # url(r'^sunny/', include('sunny.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    # Custom URLs
    url(r'^graph/', include('graph.urls', namespace='graph')),
    url(r'^getfile/(?P<pk>\d+)', getfile, name='getfile'),
    url(r'^getimages/(?P<pk>\d+)', getimages, name='getimages'),
)
