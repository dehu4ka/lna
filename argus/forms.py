from django import forms
from argus.models import ASTU


class ArgusFileUploadForm(forms.Form):
    file = forms.FileField(required=True, label='Выберите файл')
    file.widget.attrs = {
        'class': 'custom-file',
        'accept': '.csv'
    }
    tech_choices = (('', ''), ('1', 'ADSL'), ('2', 'GPON'), ('3', 'FTTx'), ('4', 'АСТУ'))
    tech = forms.ChoiceField(widget=forms.Select(), choices=tech_choices, label='Выбор технологии', required=True)
    tech.widget.attrs = {
        'class': 'custom-select',

    }


class ArgusSearchForm(forms.Form):
    input_string = forms.CharField(widget=forms.TextInput, label='')
    input_string.widget.attrs = {
        'placeholder': 'Логин, телефон или ФИО',
        'class': 'form-control'
    }


class ASTUSearchForm(forms.Form):

    @staticmethod
    def get_some_tuples_from_ASTU(field_name, label):
        field_dict = dict()
        field_objects = ASTU.objects.order_by(field_name).distinct(field_name)
        field_dict[''] = label
        for obj in field_objects:
            field_dict[getattr(obj, field_name)] = getattr(obj, field_name)
        return tuple(field_dict.items())

    input_string = forms.CharField(widget=forms.TextInput, label='', required=False)
    input_string.widget.attrs = {
        'placeholder': 'hostname/ip/адрес',
        'class': 'form-control',
        'size': 13
    }

    # partyhard =)
    vendor = forms.ChoiceField(
        widget=forms.Select(),
        choices=get_some_tuples_from_ASTU.__func__('vendor', 'Производитель'),
        label='', required=False
    )
    model = forms.ChoiceField(
        widget=forms.Select(),
        choices=get_some_tuples_from_ASTU.__func__('model', 'Модель'),
        label='', required=False
    )
    segment = forms.ChoiceField(
        widget=forms.Select(),
        choices=get_some_tuples_from_ASTU.__func__('segment', 'Сегмент'),
        label='', required=False
    )
    status = forms.ChoiceField(
        widget=forms.Select(),
        choices=get_some_tuples_from_ASTU.__func__('status', 'Статус'),
        label='', required=False
    )

    status.widget.attrs = {'class': 'custom-select custom-select-sm'}
    model.widget.attrs = {'class': 'custom-select custom-select-sm'}
    vendor.widget.attrs = {'class': 'custom-select custom-select-sm'}
    segment.widget.attrs = {'class': 'custom-select custom-select-sm'}

    def __init__(self, *args, **kwargs):
        super(ASTUSearchForm, self).__init__(*args, **kwargs)
        self.initial['status'] = 'эксплуатация'
