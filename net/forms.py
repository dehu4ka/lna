from django import forms

class TaskForm(forms.Form):
    task_status_choices = (('', ''), ('STARTED', 'STARTED'), ('SUCCESS', 'SUCCESS'),
                           ('IN PROGRESS', 'IN PROGRESS'), ('PENDING', 'PENDING'), ('ARCHIVED', 'ARCHIVED'))
    task_status = forms.ChoiceField(choices=task_status_choices, required=False, label='Выбрать статус задания')
    task_status.widget.attrs = {'class': 'custom-select', }


class ArchiveTasksForm(forms.Form):
    pass
