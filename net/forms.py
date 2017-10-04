from django import forms


class TaskForm(forms.Form):
    task_status_choices = (('', ''), ('STARTED', 'STARTED'), ('SUCCESS', 'SUCCESS'),
                           ('IN PROGRESS', 'IN PROGRESS'), ('PENDING', 'PENDING'), ('ARCHIVED', 'ARCHIVED'),
                           ('TERMINATED', 'TERMINATED'))
    task_status = forms.ChoiceField(choices=task_status_choices, required=False, label='Выбрать статус задания')
    task_status.widget.attrs = {'class': 'custom-select', }


class ArchiveTasksForm(forms.Form):
    pass


class SubnetForm(forms.Form):
    subnets = forms.CharField(widget=forms.Textarea, required=True, label='')
    discover_task_choices = (('fping', 'Discover with FPING'), ('vendor', 'Discover Vendor and models'))
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
        'placeholder': 'search IP or Subnet',
        'class': 'form-control',
        'size': 14,
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

