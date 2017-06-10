from django.shortcuts import render
from django.views.generic import TemplateView, FormView, UpdateView, ListView
from .forms import ArgusFileUploadForm, ArgusSearchForm
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from .argus_lib import parse_adsl_csv, parse_fttx_csv, parse_gpon_csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.shortcuts import render, HttpResponse, redirect
from el_pagination.views import AjaxListView
from .models import ArgusADSL


# Create your views here.
# Загрузка из CSV файла
#@login_required()
class ADSLImport(LoginRequiredMixin, TemplateView):
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
            if tech == '1':
                counter = parse_adsl_csv(file_path)
            elif tech == '2':
                counter = parse_gpon_csv(file_path)
            elif tech == '3':
                counter = parse_fttx_csv(file_path)
            else:
                messages.add_message(request, messages.ERROR, 'Выбрана непонятная технология включения')

            messages.add_message(request, messages.INFO, 'Добавлено ' + str(counter) + ' записей')
        else:
            messages.add_message(request, messages.ERROR, "Ошибка")
            messages.add_message(request, messages.ERROR, form.errors)
            pass

        # New Form
        form = ArgusFileUploadForm()
        args = {'form': form}
        return render(request, self.template_name, args)


class ADSLView(LoginRequiredMixin, AjaxListView, FormView):
    context_object_name = 'argus_list'
    template_name = 'argus/adsl_view.html'
    page_template = 'argus/adsl_view_list_page.html'
    form_class = ArgusSearchForm
    success_url = '/argus/adsl'

    @classmethod
    def get_filter_by_search(cls, query):
        print(query)
        if query[:4] == '7789':
            return ArgusADSL.objects.filter(inet_login__contains=query).order_by('inet_login')
        if query[:5] == '77089':
            return ArgusADSL.objects.filter(iptv_login__contains=query).order_by('iptv_login')
        if query[:3] == '349':
            return ArgusADSL.objects.filter(tel_num__contains=query).order_by('tel_num')
        return ArgusADSL.objects.filter(fio__contains=query).order_by('fio')

    def get_queryset(self):
        if self.request.method == 'POST':
            form = ArgusSearchForm(self.request.POST)
            if form.is_valid():
                query = form.cleaned_data['input_string']
                return self.get_filter_by_search(query)
        if self.request.method == 'GET':
            input_string = self.request.GET.get('search')
            if input_string:
                return self.get_filter_by_search(input_string)

        return ArgusADSL.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super(ADSLView, self).get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['form'] = ArgusSearchForm(self.request.POST)
            context['search'] = self.request.POST['input_string']
        else:
            context['form'] = ArgusSearchForm
        context['fluid_container'] = True
        return context

    """def form_valid(self, form):
        print(form.cleaned_data)
        return super(ADSLView, self).form_valid(form)"""

    # OMFG!!!
    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


    #def get(self, request, *args, **kwargs):
    #    return super(ADSLView, self).get(request, *args, **kwargs)
