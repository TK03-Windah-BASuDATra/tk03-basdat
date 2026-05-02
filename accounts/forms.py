from django import forms


ROLE_CHOICES = [
    ('customer', 'Customer'),
    ('organizer', 'Organizer'),
    ('admin', 'Admin'),
]


def widget_attrs(placeholder):
    return {
        'class': 'form-control',
        'placeholder': placeholder,
    }


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs=widget_attrs('Masukkan username')),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs=widget_attrs('Masukkan password')),
    )
    role = forms.ChoiceField(
        label='Masuk sebagai',
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class BaseRegisterForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs=widget_attrs('Pilih username')),
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs=widget_attrs('Masukkan password')),
    )
    password2 = forms.CharField(
        label='Konfirmasi Password',
        widget=forms.PasswordInput(attrs=widget_attrs('Konfirmasi password')),
    )
    agree_terms = forms.BooleanField(
        required=True,
        label='',
        error_messages={'required': 'Anda harus menyetujui Syarat & Ketentuan.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Password tidak cocok.')
        return cleaned


class CustomerOrganizerRegisterForm(BaseRegisterForm):
    full_name = forms.CharField(
        label='Nama Lengkap',
        widget=forms.TextInput(attrs=widget_attrs('Masukkan nama lengkap')),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs=widget_attrs('Masukkan email')),
    )
    phone_number = forms.CharField(
        label='Nomor Telepon',
        widget=forms.TextInput(attrs=widget_attrs('Masukkan nomor telepon')),
    )

    field_order = ['full_name', 'email', 'phone_number', 'username', 'password1', 'password2', 'agree_terms']


class AdminRegisterForm(BaseRegisterForm):
    pass