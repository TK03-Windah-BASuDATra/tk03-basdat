from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class BaseRegisterForm(UserCreationForm):
    agree_terms = forms.BooleanField(
        required=True,
        label="",
        error_messages={
            "required": "Anda harus menyetujui Syarat & Ketentuan."
        },
    )

    class Meta:
        model = User
        fields = ["username", "password1", "password2", "agree_terms"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].label = "Username"
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Konfirmasi Password"

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
        self.fields["agree_terms"].widget.attrs.update({
            "class": "form-check-input",
        })

        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

    def save(self, commit=True, role="customer"):
        user = super().save(commit=False)
        user.role = role

        if commit:
            user.save()

        return user


class CustomerOrganizerRegisterForm(BaseRegisterForm):
    full_name = forms.CharField(max_length=150, label="Nama Lengkap")
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(max_length=20, label="Nomor Telepon")

    class Meta(BaseRegisterForm.Meta):
        fields = [
            "full_name",
            "email",
            "phone_number",
            "username",
            "password1",
            "password2",
            "agree_terms",
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

    def save(self, commit=True, role="customer"):
        user = super().save(commit=False, role=role)

        full_name = self.cleaned_data["full_name"]
        name_parts = full_name.split(" ", 1)

        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        user.email = self.cleaned_data["email"]

        if hasattr(user, "phone_number"):
            user.phone_number = self.cleaned_data["phone_number"]

        if commit:
            user.save()

        return user


class AdminRegisterForm(BaseRegisterForm):
    class Meta(BaseRegisterForm.Meta):
        fields = [
            "username",
            "password1",
            "password2",
            "agree_terms",
        ]