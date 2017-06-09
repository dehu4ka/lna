from django.shortcuts import render
from django.views.generic import TemplateView
from .forms import ArgusFileUploadForm
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from .argus_lib import parse_adsl_csv


# Create your views here.
# Загрузка из CSV файла
class ADSL_Import(TemplateView):
    template_name = 'argus/adsl.html'

    def get(self, request, *args, **kwargs):
        form = ArgusFileUploadForm()

        args = {
            'form': form
        }
        return render(request, self.template_name, args)

    def post(self, request):
        form = ArgusFileUploadForm(request.POST, request.FILES)
        # messages.add_message(request, messages.INFO, 'Попытка загрузки файла')

        if form.is_valid():
            uploaded_file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.url(filename)
            messages.add_message(request, messages.INFO, 'File was uploaded to '+file_path)
            parse_adsl_csv(file_path)

        else:
            messages.add_message(request, messages.ERROR, "Ошибка")
            messages.add_message(request, messages.ERROR, form.errors)
            pass

        args = {'form' : form }
        return render(request, self.template_name, args)

