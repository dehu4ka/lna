from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .tasks import long_job
from .lib import get_ne_json


# Create your views here.
class Demo(LoginRequiredMixin, TemplateView):
    template_name = 'net/demo.html'

    def get(self, request, *args, **kwargs):
        task = long_job.delay(111, 111)
        # print("task id is " + task.id)
        # super(Demo, self).get(request, *args, **kwargs)
        return render(request, self.template_name, *args, **kwargs)

class PickNE(LoginRequiredMixin, TemplateView):
    template_name = 'net/pick_ne.html'

    def get_context_data(self, **kwargs):
        context = super(PickNE, self).get_context_data(**kwargs)
        context['test'] = get_ne_json()
        return context


