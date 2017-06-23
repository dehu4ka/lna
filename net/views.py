from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .tasks import long_job, job_starter
from django.core.exceptions import PermissionDenied
from .models import Scripts
from argus.models import ASTU

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
        possible_scripts = Scripts.objects.all()
        context['possible_scripts'] = possible_scripts
        return context


class DoTask(LoginRequiredMixin, TemplateView):
    template_name = 'net/do_task.html'

    def get(self, *args, **kwargs):
        raise PermissionDenied

    def post(self, request):
        destinations_ids = request.POST.getlist('destinations')
        script_id = request.POST['script_select']
        script_obj = Scripts.objects.get(pk=script_id)
        script_name = script_obj.name
        script_descr = script_obj.description
        class_name = script_obj.class_name

        ne_list = list()  # список объектов и скриптов для передачи в контекст

        for dst in destinations_ids:
            ne=ASTU.objects.get(pk=dst)
            ne_list.append(ne)
            #  Запуск работы
            job_starter.delay(dst, script_id)
        # context
        args = dict()
        args['ne_list'] = ne_list
        args['script_name'] = script_name
        args['script_descr'] = script_descr
        args['class_name'] = class_name

        return render(request, self.template_name, args)
