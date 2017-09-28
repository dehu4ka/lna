from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, FormView
from django.core.exceptions import PermissionDenied
from net.models import Scripts, Job, Equipment
from net.forms import TaskForm, ArchiveTasksForm, SubnetForm, NEListForm
from django.contrib import messages
from net.equipment.generic import GenericEquipment
from net.lib import celery_job_starter, scan_nets_with_fping, discover_vendor
from argus.models import Client, ASTU


# Create your views here.
class Demo(LoginRequiredMixin, TemplateView):
    template_name = 'net/demo.html'

    def get(self, request, *args, **kwargs):
        eq_device = Equipment.objects.get(ne_ip='10.205.18.247')  # equipment object
        eq = GenericEquipment(eq_device)
        eq.set_io_timeout(1)
        eq.suggest_login(resuggest=False)
        eq.do_login()
        eq.discover_vendor()
        return render(request, self.template_name, *args, **kwargs)


class PickNE(LoginRequiredMixin, TemplateView):
    template_name = 'net/pick_ne.html'

    def get_context_data(self, **kwargs):
        context = super(PickNE, self).get_context_data(**kwargs)
        possible_scripts = Scripts.objects.all().exclude(is_hidden=True)
        context['possible_scripts'] = possible_scripts
        return context


class DoTask(LoginRequiredMixin, TemplateView):
    template_name = 'net/do_task.html'

    def get(self, *args, **kwargs):
        raise PermissionDenied

    def post(self, request):
        """
        Нужно запустить стартер, который получит на вход список ID назначений, имя скрипта для выполнения, и возможно,
        какие-то дополнительные аргументы.

        :param request:

        :return:
        """
        destinations_ids = request.POST.getlist('destinations')
        script_id = request.POST['script_select']
        celery_job_starter(destinations_ids, script_id)
        args = dict()
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


class DiscoverSubnets(LoginRequiredMixin, FormView):
    template_name = 'net/discover_subnets.html'
    form_class = SubnetForm

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DiscoverSubnets, self).get_context_data(**kwargs)
        context['new'] = False
        context['found'] = False
        if self.request.method == 'POST':
            form = SubnetForm(self.request.POST)
            if form.is_valid():
                subnets = form.cleaned_data['subnets'].split("\r\n")  # lists with subnet
                cast_to_celery = form.cleaned_data['cast_to_celery']  # "Send discovery task to Celery" checkbox
                discover_task = form.cleaned_data['discover_task']  # Task type
                context['cast_to_celery'] = cast_to_celery
                if discover_task == 'fping':
                    if not cast_to_celery:
                        found, new = scan_nets_with_fping(subnets)
                        context['found'] = found
                        context['new'] = new
                    else:
                        celery_job_starter(subnets, '999')  # 999 will be send task to celery for subnets scan
                if discover_task == 'vendor':
                    if not cast_to_celery:
                        discover_vendor(subnets)
                    else:
                        celery_job_starter(subnets, '1000')
                    pass
        return context


class ClientsCount(LoginRequiredMixin, TemplateView):
    template_name = 'net/clients_count.html'

    def get_context_data(self, **kwargs):
        result_dict = dict()

        clients = Client.objects.all()
        for client in clients:
            hostname = client.hostname
            hostname_parts = hostname.split('-')
            try:
                node_name = hostname_parts[0] + '-' + hostname_parts[1] + '-' + hostname_parts[2]
                if node_name in result_dict:
                    result_dict[node_name] += 1
                else:
                    result_dict[node_name] = 1
            except IndexError:
                # skip
                # print(hostname)
                pass

        result_str = ''
        for node in result_dict:
            try:
                astu_objects = ASTU.objects.filter(hostname__contains=node).filter(status='эксплуатация')
                astu_first_object = astu_objects[0]
                address = astu_first_object.address
            except IndexError:
                address = 'Unknown'
            # print(node + ';' + str(result_dict[node]) + ';"' + address + '"')
            result_str += node + ';' + str(result_dict[node]) + ';"' + address + '"' + "\n"
        context = super(ClientsCount, self).get_context_data(**kwargs)
        context['result_str'] = result_str
        return context


class NEList(LoginRequiredMixin, ListView, FormView):
    template_name = 'net/ne_list.html'
    form_class = NEListForm
    model = Equipment
    success_url = 'net/ne_list'
    paginate_by = 20
    context_object_name = 'ne_list'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_queryset(self):
        ne_list = Equipment.objects.all()

        if self.request.method == 'POST':
            form = NEListForm(self.request.POST)
            if form.is_valid():
                is_login_discovered = form.cleaned_data['is_login_discovered']
                ne_list = ne_list.filter(credentials_id__isnull=False) if is_login_discovered else ne_list
                is_vendor_discovered = form.cleaned_data['is_vendor_discovered']
                ne_list = ne_list.filter(vendor__isnull=False) if is_vendor_discovered else ne_list

        if self.request.method == 'GET':
            is_login_discovered = self.request.GET.get('is_login_discovered')
            ne_list = ne_list.filter(credentials_id__isnull=False) if \
                (is_login_discovered or is_login_discovered == 'None') else ne_list
            is_vendor_discovered = self.request.GET.get('is_login_discovered')
            ne_list = ne_list.filter(vendor__isnull=False) if \
                (is_vendor_discovered or is_vendor_discovered == 'None') else ne_list
        return ne_list

    def get_context_data(self, **kwargs):
        context = super(NEList, self).get_context_data(**kwargs)
        context['row_count'] = self.get_queryset().count()
        if self.request.method == 'GET':
            if self.request.GET.get('is_login_discovered') == 'True':
                context['is_login_discovered'] = 'True'
            if self.request.GET.get('is_vendor_discovered') == 'True':
                context['is_vendor_discovered'] = 'True'
        if self.request.method == 'POST':
            form = NEListForm(self.request.POST)
            if form.is_valid():
                context['is_login_discovered'] = form.cleaned_data['is_login_discovered']
                context['is_vendor_discovered'] = form.cleaned_data['is_vendor_discovered']

        return context


