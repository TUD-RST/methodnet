from django.conf.urls import url
from django.urls import path, re_path
from . import views

urlpatterns = [
  url(r'^$', views.LandingPageView.as_view(), name='landing-page'),
  path('g/<slug:graph>', views.GraphEditorView.as_view(), name='graph-editor')
]

