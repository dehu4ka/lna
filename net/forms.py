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
    subnets.widget.attrs = {
        'placeholder': "Enter the networks to scan with fping in CIDR format\n3 x /24 is OK.\n"
                       "For more network scan, please push checkbox \"send task to Celery\"\n"
                       "/24 scan took about 30 second, so /16 will be about 1/2 hour",
        'rows': 5,
        'cols': 40,
        'class': 'form-control',

    }
    cast_to_celery = forms.BooleanField(label='Send discovery task to Celery ', required=False)
    sh_ip_bgp = forms.BooleanField(label='output from "sh ip bgp" ', required=False)
