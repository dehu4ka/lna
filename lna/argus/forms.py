from django import forms


class ArgusFileUploadForm(forms.Form):
    file = forms.FileField(required=True, label='Выберите файл')
    file.widget.attrs = {
        'class': 'custom-file',
        'accept': '.csv'
    }
    tech_choices = (('', ''), ('1', 'ADSL'), ('2', 'GPON'), ('3', 'FTTx'))
    tech = forms.ChoiceField(widget=forms.Select(), choices=tech_choices, label='Выбор технологии', required=True)
    tech.widget.attrs={
        'class': 'custom-select',

    }
