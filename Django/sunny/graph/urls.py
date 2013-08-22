from django.conf.urls import patterns, url

from graph import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^response.json/?$', views.json_response, name='json_response'),
)

