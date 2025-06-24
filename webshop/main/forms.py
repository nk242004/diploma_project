from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from captcha.fields import CaptchaField

from .models import AdvUser, SuperRubric, SubRubric, Bb, AdditionalImage, Comment
from .signals import post_register

class ProfileEditForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Email address')

    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'first_name', 'last_name',
                  'send_messages')

class RegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Email address')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput,
      help_text=password_validation.password_validators_help_text_html())
    password2 = forms.CharField(label='Password (repeat)',
      widget=forms.PasswordInput,
      help_text='Enter password again for correction')

    # def clean_password1(self):
    #     password1 = self.cleaned_data['password1']
    #     if password1:
    #         password_validation.validate_password(password1)
    #     return password1

    def clean(self):
        super().clean()
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password1 != password2:
            errors = {'password2': ValidationError(
              'Passwords are not the same', code='password_mismatch')}
            raise ValidationError(errors)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        user.is_activated = False
        if commit:
            user.save()
        post_register.send(RegisterForm, instance=user)
        return user

    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'password1', 'password2',
                  'first_name', 'last_name', 'send_messages')

class SubRubricForm(forms.ModelForm):
    super_rubric = forms.ModelChoiceField(
                   queryset=SuperRubric.objects.all(), empty_label=None,
                   label='SuperRubric', required=True)

    class Meta:
        model = SubRubric
        fields = '__all__'

class SearchForm(forms.Form):
    keyword = forms.CharField(required=False, max_length=20, label='')

class BbForm(forms.ModelForm):
    class Meta:
        model = Bb
        fields = '__all__'
        widgets = {'author': forms.HiddenInput}

AIFormSet = forms.inlineformset_factory(Bb, AdditionalImage, fields='__all__')

class UserCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ('is_active',)
        widgets = {'bb': forms.HiddenInput}

class GuestCommentForm(forms.ModelForm):
    captcha = CaptchaField(label='Enter text from picture',
                     error_messages={'invalid': 'Incorrect text'})

    class Meta:
        model = Comment
        exclude = ('is_active',)
        widgets = {'bb': forms.HiddenInput}
