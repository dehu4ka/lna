from django.shortcuts import render
from django.views.generic import TemplateView, FormView, UpdateView, ListView
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render, HttpResponse, redirect
from el_pagination.views import AjaxListView
from el_pagination.decorators import page_template
from .models import ArgusADSL, ArgusFTTx, ArgusGPON, ASTU, Client
from .forms import ArgusFileUploadForm, ArgusSearchForm, ASTUSearchForm
from .argus_lib import parse_adsl_csv, parse_fttx_csv, parse_gpon_csv, parse_astu_csv, ip_pattern
import re


# Create your views here.
# Загрузка из CSV файла
class ClientImport(LoginRequiredMixin, TemplateView):
    template_name = 'argus/adsl.html'

    def get(self, request, *args, **kwargs):
        form = ArgusFileUploadForm()
        args = {'form': form}
        return render(request, self.template_name, args)

    def post(self, request):
        form = ArgusFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.url(filename)
            messages.add_message(request, messages.INFO, 'File was uploaded to '+file_path)
            # Check tech | технология подключения
            tech = form.cleaned_data['tech']
            counter = '0'
            ignored = '0'
            if tech == '1':
                counter = parse_adsl_csv(file_path)
            elif tech == '2':
                counter, ignored = parse_gpon_csv(file_path)
            elif tech == '3':
                counter, ignored = parse_fttx_csv(file_path)
            elif tech == '4':
                counter, ignored = parse_astu_csv(file_path)
            else:
                messages.add_message(request, messages.ERROR, 'Выбрана непонятная технология включения')

            messages.add_message(request, messages.INFO,
                                 'Добавлено ' + str(counter) + ' записей. Проигнорировано - ' + str(ignored))
        else:
            messages.add_message(request, messages.ERROR, "Ошибка")
            messages.add_message(request, messages.ERROR, form.errors)
            pass

        # New Form
        form = ArgusFileUploadForm()
        args = {'form': form}
        return render(request, self.template_name, args)


class ASTUView(LoginRequiredMixin, FormView, ListView):
    context_object_name = 'astu_list'
    template_name = 'argus/astu.html'
    form_class = ASTUSearchForm
    success_url = '/argus/astu'
    model = ASTU

    def get_queryset(self):
        if self.request.method == 'POST':
            form = ASTUSearchForm(self.request.POST)
            if form.is_valid():
                input_string = form.cleaned_data['input_string']
                status = form.cleaned_data['status']
                vendor = form.cleaned_data['vendor']
                model = form.cleaned_data['model']
                segment = form.cleaned_data['segment']

                search_objects = ASTU.objects.all()

                if input_string:
                    if re.findall(ip_pattern, input_string):
                        search_objects = ASTU.objects.filter(ne_ip=input_string)
                    else:
                        search_objects = ASTU.objects.filter(
                            Q(hostname__icontains=input_string) |
                            Q(address__icontains=input_string)
                        )
                if status:
                    search_objects = search_objects.filter(status=status)
                if vendor:
                    search_objects = search_objects.filter(vendor=vendor)
                if model:
                    search_objects = search_objects.filter(model=model)
                if segment:
                    search_objects = search_objects.filter(segment=segment)
                return search_objects
            else:
                messages.add_message(self.request, messages.ERROR, form.errors)

        return ASTU.objects.all().filter(status__exact='эксплуатация')[:5]

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ASTUView, self).get_context_data(**kwargs)
        # context['fluid_container'] = True
        context['row_count'] = self.get_queryset().count() or 0
        return context


class SearchView(LoginRequiredMixin, AjaxListView, FormView):
    template_name = 'argus/search_view.html'
    form_class = ArgusSearchForm
    success_url = '/argus/find'
    page_template = 'argus/search_view_list_page.html'

    def get_queryset(self):
        return None

    # OMFG!!!
    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['page_template'] = self.page_template
        if self.request.method == 'POST':
            context['search'] = self.request.POST['input_string']
            context['results'] = self.get_results(self.request.POST['input_string'])
            context['form'] = ArgusSearchForm(self.request.POST)
        else:
            context['search'] = self.request.GET.get('search')
            context['results'] = self.get_results(self.request.GET.get('search'))
            context['form'] = ArgusSearchForm()
        context['fluid_container'] = True
        context['gpon_page'] = 'gpon_page'
        return context

    def get_results(self, input_string=None):
        search_objects = Client.objects.all().order_by('id')
        count = 15
        if input_string:
            if re.findall(ip_pattern, input_string):
                search_objects = search_objects.filter(ne_ip=input_string)

            else:
                search_objects = search_objects.filter(
                    Q(inet_login__contains=input_string) |
                    Q(iptv_login__contains=input_string) |
                    Q(tel_num__contains=input_string) |
                    Q(address__icontains=input_string) |
                    Q(fio__icontains=input_string) |
                    Q(hostname__icontains=input_string)
                )
                count = search_objects.count()
            return {'search_objects': search_objects, 'count': count}
        return {'search_objects': search_objects[:15], 'count': count}


