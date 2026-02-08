from django.forms import ModelForm, TextInput, PasswordInput
from django.forms.fields import CharField

# from jsonserv.core.models import FormField
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from jsonserv.core.models import UserSession


class CustomAuthenticationForm(AuthenticationForm):
    """Модификация атрибутов формы входа"""
    # Добавление класса к полям формы для качественной визуализации
    username = CharField(widget=TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'})
    )
    password = CharField(widget=PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )


class UserSessionFrom(ModelForm):
    # Дополнительное свойство Примечание при входе
    class Meta:
        model = UserSession
        fields = ['comment']
        widgets = {
            'comment': TextInput(attrs={'placeholder': 'Примечание'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserSessionFrom, self).__init__(*args, **kwargs)
        # Добавление класса к полям формы для качественной визуализации
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class CustomPasswordChangeForm(PasswordChangeForm):
    """Модификация атрибутов формы смены пароля"""
    # Добавление класса к полям формы для качественной визуализации
    new_password1 = CharField(widget=PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Новый пароль'})
    )
    new_password2 = CharField(widget=PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Новый пароль повторно'})
    )
    old_password = CharField(widget=PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Текущий пароль'})
    )