from django import forms


class ArgusFileUploadForm(forms.Form):
    file = forms.FileField(required=True, label='Выберите файл')
    file.widget.attrs = {
        'class': 'custom-file',
        'accept': '.csv'
    }
    tech_choices = (('', ''), ('1', 'ADSL'), ('2', 'GPON'), ('3', 'FTTx'), ('4', 'АСТУ'))
    tech = forms.ChoiceField(widget=forms.Select(), choices=tech_choices, label='Выбор технологии', required=True)
    tech.widget.attrs={
        'class': 'custom-select',

    }


class ArgusSearchForm(forms.Form):
    input_string = forms.CharField(widget=forms.TextInput, label='')
    input_string.widget.attrs = {
        'placeholder': 'Логин, телефон или ФИО',
        'class': 'form-control'
    }

class ASTUSearchForm(forms.Form):
    # поле для ввода повседневной информации
    input_string = forms.CharField(widget=forms.TextInput, label='', required=False)
    input_string.widget.attrs = {
        'placeholder': 'hostname / ip / адрес',
        'class': 'form-control'
    }
    # выбор только активного оборудование (в статусе эксплуатация)
    is_active = forms.CharField(widget=forms.CheckboxInput, label='Только в статусе эксплуатация', required=False)
    is_active.widget.attrs = {
        'class': 'checkbox'
    }
