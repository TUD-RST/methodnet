from django.conf.urls import url
from django.urls import path, re_path
from . import views

urlpatterns = [
  url(r'^$', views.LandingPageView.as_view(), name='landing-page'),

  # placeholders
  path('imprint', views.LandingPageView.as_view(), name='imprint-page'),
  path('privacy', views.LandingPageView.as_view(), name='privacy-page'),
  path('contact', views.LandingPageView.as_view(), name='contact-page'),
  ]

