from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _



User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=254, widget=forms.EmailInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _( "EMAIL" )}))
    first_name = forms.CharField(required=True, max_length=50, widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _( "FIRST NAME" )}))
    last_name = forms.CharField(required=True, max_length=50, widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _( "LAST NAME" )}))
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _( "PASSWORD" )})
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _( "CONFIRM PASSWORD" )})
    )


    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("This email is already in use."))
        return email
    

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = None
        if commit:
            user.save()
        return user
    

class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(label=_( "Email" ), widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _( "EMAIL" )}))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("PASSWORD")})
    )

     
    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_("Invalid email or password."))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive."))
        return self.cleaned_data


class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', _("Enter a valid phone number."))],
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("PHONE NUMBER")})
    )
    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("FIRST NAME")})
    )
    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("LAST NAME")})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("EMAIL")})
    )


    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'company', 
                  'address1', 'address2', 'city', 'country',
                  'province', 'postal_code', 'phone')
        widgets = {
            'company': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("COMPANY")}),
            'address1': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("ADDRESS LINE 1")}),
            'address2': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("ADDRESS LINE 2")}),
            'city': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("CITY")}),
            'country': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("COUNTRY")}),
            'province': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("PROVINCE")}),
            'postal_code': forms.TextInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("POSTAL CODE")}),
        }
        
class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="",
        widget=forms.EmailInput(attrs={
            'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500',
            'placeholder': _("EMAIL")
        })
    )



class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("NEW PASSWORD")})
    )
    new_password2 = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput(attrs={'class': 'dotted-input w-full py-3 text-sm font-medium text-gray-900 placeholder-gray-500', 'placeholder': _("CONFIRM PASSWORD")})
    )

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("new_password1")
        pw2 = cleaned_data.get("new_password2")

        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError(_("Passwords do not match."))
        return cleaned_data