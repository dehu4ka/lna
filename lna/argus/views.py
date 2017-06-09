from django.shortcuts import render
from django.views.generic import TemplateView
from .forms import ArgusFileUploadForm
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
class ADSL_Import(LoginRequiredMixin, TemplateView):
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
            if tech == '1':
                parse_adsl_csv(file_path)
            elif tech == '2':
                parse_gpon_csv(file_path)
            elif tech == '3':
                parse_fttx_csv(file_path)
            else:
                messages.add_message(request, messages.ERROR, 'Выбрана непонятная технология включения')
        else:
            messages.add_message(request, messages.ERROR, "Ошибка")
            messages.add_message(request, messages.ERROR, form.errors)
            pass

        # New Form
        form = ArgusFileUploadForm()
        args = {'form' : form }
        return render(request, self.template_name, args)


class ADSL_View(AjaxListView):
    context_object_name = 'argus_list'
    template_name = 'argus/adsl_view.html'
    page_template = 'argus/adsl_view_list_page.html'

    def get_queryset(self):
        return ArgusADSL.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ADSL_View, self).get_context_data(**kwargs)
        context['fluid_container'] = True
        context['form'] = ArgusFileUploadForm
        return context

