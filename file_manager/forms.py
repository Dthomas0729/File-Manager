from django.forms import ModelForm, Textarea, EmailInput, Select, NumberInput
from .models import Customer, RentalOrder
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CustomerForm(ModelForm):

    class Meta:
        model = Customer
        fields = '__all__'

        widgets = {
            'email': EmailInput(),
        }
        labels = {
            'apt_suite_other': _('Apt/Suite/Other'),
        }

class RentalOrderForm(ModelForm):

    class Meta:
        model = RentalOrder
        fields = '__all__'

