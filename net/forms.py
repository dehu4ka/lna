from django import forms
from net.models import Equipment


class TaskForm(forms.Form):
    task_status_choices = (('', ''), ('STARTED', 'STARTED'), ('SUCCESS', 'SUCCESS'),
                           ('IN PROGRESS', 'IN PROGRESS'), ('PENDING', 'PENDING'), ('ARCHIVED', 'ARCHIVED'),
                           ('TERMINATED', 'TERMINATED'))
    task_status = forms.ChoiceField(choices=task_status_choices, required=False, label='Выбрать статус задания')
    task_status.widget.attrs = {'class': 'custom-select', }


class ArchiveTasksForm(forms.Form):
    pass


class SubnetForm(forms.Form):
    subnets = forms.CharField(widget=forms.Textarea, required=False, label='')
    discover_task_choices = (('fping', 'Discover with FPING'), ('vendor', 'Discover Vendor and models'),
                             ('config', "Get Config from NE's"), ('put_syslocation', 'Put syslocation from ASTU'))
    subnets.widget.attrs = {
        'placeholder': "Enter the networks to scan with fping in CIDR format\n3 x /24 is OK.\n"
                       "For more network scan, please push checkbox \"send task to Celery\"\n"
                       "/24 scan took about 30 second, so /16 will be about 1/2 hour",
        'rows': 5,
        'cols': 40,
        'class': 'form-control',

    }
    cast_to_celery = forms.BooleanField(label='Send discovery task to Celery ', required=False)
    discover_task = forms.ChoiceField(choices=discover_task_choices, required=True, label='Choice task Type')
    discover_task.widget.attrs = {'class': 'custom-select', }


class NEListForm(forms.Form):
    ip_or_subnet = forms.CharField(widget=forms.TextInput, label='', required=False)
    ip_or_subnet.widget.attrs = {
        'placeholder': 'IP/Subnet/Hostname',
        'class': 'form-control m-1',
        # 'size': 15,
    }

    LOGIN_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('any', "Don't care")
    ]
    is_login_discovered = forms.CharField(widget=forms.RadioSelect(choices=LOGIN_CHOICES),
                                          required=False, initial='no')

    VENDOR_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('any', "Don't care")
    ]

    is_vendor_discovered = forms.CharField(widget=forms.RadioSelect(choices=VENDOR_CHOICES), required=False)


class ConfigSearchForm(forms.Form):
    search = forms.CharField(max_length=64, required=True, min_length=3)  # min 3 char for search
    search.widget.attrs = {
        'placeholder': 'Search term',
        'class': 'form-control',
    }


class CMDRunnerForm(forms.Form):
    ips_textfield = forms.CharField(widget=forms.Textarea, required=False, label='')
    ips_textfield.widget.attrs = {
        'placeholder': "Enter IP's of equipment or select NE vendor below",
        'class': 'form-control m-1',
        # 'size': 15,
    }
    distinct_objects = Equipment.objects.all().order_by('vendor').distinct('vendor').filter(vendor__isnull=False)
    vendor_choices_values_list = list()
    vendor_choices_values_list.append(('', ''))
    for obj in distinct_objects:
        vendor_choices_values_list.append(tuple((obj.vendor, obj.vendor)))
    vendor_choices_values = tuple(vendor_choices_values_list)
    vendor_choices = forms.ChoiceField(choices=vendor_choices_values, required=True,
                                       label='Run task for all NE from this vendor')
    vendor_choices.widget.attrs = {'class': 'custom-select', }
    commands_list = forms.CharField(widget=forms.Textarea, required=False, label='')
    commands_list.widget.attrs = {
        'placeholder': 'Commands to execute',
        'class': 'form-control m-1',
        'rows': 15,
    }
