from django.shortcuts import render
from django.views import View
from django.template.response import TemplateResponse


class LandingPageView(View):

    # noinspection PyMethodMayBeStatic
    def get(self, request):

        context = {"title": "Landing Page"}

        return TemplateResponse(request, "ackbas_core/landing.html", context)
