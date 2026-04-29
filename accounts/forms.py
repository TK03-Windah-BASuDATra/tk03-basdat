from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=150, label="Nama Lengkap")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(max_length=20, label="Nomor Telepon")

    class Meta:
        model = User
        fields = [
            "full_name",
            "email",
            "phone_number",
            "username",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["full_name"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "placeholder": "Masukkan nama lengkap",
        })
        self.fields["email"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "placeholder": "Masukkan email",
        })
        self.fields["phone_number"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "placeholder": "Masukkan nomor telepon",
        })
        self.fields["username"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "placeholder": "Pilih username",
        })
        self.fields["password1"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "placeholder": "Masukkan password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-control form-control-lg",
            "placeholder": "Konfirmasi password",
        })

    def save(self, commit=True, role="customer"):
        user = super().save(commit=False)

        full_name = self.cleaned_data["full_name"]
        name_parts = full_name.split(" ", 1)

        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.role = role

        if commit:
            user.save()

        return user