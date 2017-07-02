from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, FormView
from net.tasks import long_job, job_starter
from net.scripts.long import start as long
from django.core.exceptions import PermissionDenied
from net.models import Scripts, Job, Equipment, Credentials
from argus.models import ASTU
from lna.taskapp.celery_app import app
from net.forms import TaskForm, ArchiveTasksForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from net.equipment.generic import GenericEquipment

# Create your views here.
class Demo(LoginRequiredMixin, TemplateView):
    template_name = 'net/demo.html'

    def get(self, request, *args, **kwargs):
        cisco = Equipment.objects.get(ne_ip='10.205.18.161')
        eq = GenericEquipment(cisco)
        eq.suggest_login(resuggest=True)
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
            # job_starter.delay(dst, script_id)
            job = long.delay(dst, script_id)
            print(job.backend)
            job_object = Job()
            job_object.celery_id = job.task_id
            job_object.ne_id = ASTU.objects.get(pk=dst)
            job_object.script_name = script_name
            job_object.status = 'PENDING'
            job_object.save()

        # context
        args = dict()
        args['ne_list'] = ne_list
        args['script_name'] = script_name
        args['script_descr'] = script_descr
        args['class_name'] = class_name

        return render(request, self.template_name, args)


class ActiveTasks(LoginRequiredMixin, ListView, FormView):
    model = Job
    template_name = 'net/active_tasks.html'
    form_class = TaskForm
    paginate_by = 9
    success_url = '/net/active_tasks'


    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.method == 'POST':
            form = TaskForm(self.request.POST)
            if form.is_valid():
                task_status = form.cleaned_data['task_status']
                if task_status != '':
                    return Job.objects.filter(status=task_status)
                return Job.objects.all().exclude(status='ARCHIVED').exclude(status='TERMINATED')
        if self.request.method == 'GET':
            if self.request.GET.get('task_status') and (self.request.GET.get('task_status') != 'None'):
                return Job.objects.filter(status=self.request.GET.get('task_status'))
        return Job.objects.all().exclude(status='ARCHIVED').exclude(status='TERMINATED')

    def get_context_data(self, **kwargs):
        context = super(ActiveTasks, self).get_context_data(**kwargs)
        task_status = None
        if self.request.method == 'POST':
            form = TaskForm(self.request.POST)
            if form.is_valid():
                task_status = form.cleaned_data['task_status']
        if self.request.method == 'GET':
            task_status = self.request.GET.get('task_status')
        context['task_status'] = task_status
        return context


class ArchiveTasks(LoginRequiredMixin, FormView):
    template_name = 'net/archive_tasks.html'
    form_class = ArchiveTasksForm

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ArchiveTasks, self).get_context_data(**kwargs)
        if self.request.method == 'POST':
            Job.objects.filter(status='SUCCESS').update(status='ARCHIVED')
            messages.add_message(self.request, messages.INFO, 'Архивация выполена')
        return context


class TaskDetail(LoginRequiredMixin, TemplateView):
    template_name = 'net/task_detail.html'
