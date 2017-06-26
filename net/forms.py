from django import forms

class TaskForm(forms.Form):
    task_status_choices = (('STARTED', 'STARTED'), ('SUCCESS', 'SUCCESS'),
                           ('IN PROGRESS', 'IN PROGRESS'), ('PENDING', 'PENDING'))
    task_status = forms.ChoiceField(choices=task_status_choices)
    task_status.widget.attrs = {'class': 'custom-select', }
