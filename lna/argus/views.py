from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.
class ADSL_Import(TemplateView):
    template_name = 'argus/adsl.html'
