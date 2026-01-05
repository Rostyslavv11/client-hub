from django import forms
from django.core.exceptions import ValidationError

from accounts.models import ClientProfile, CustomUser, FreelancerProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "phone_number"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise ValidationError("Email is required.")
        qs = CustomUser.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This email is already in use.")
        return email


class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ["company_name", "location", "hire_rate", "is_open_to_agencies"]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "hire_rate": forms.NumberInput(attrs={"class": "form-control"}),
            "is_open_to_agencies": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class FreelancerProfileForm(forms.ModelForm):
    class Meta:
        model = FreelancerProfile
        fields = [
            "title",
            "hourly_rate",
            "bio",
            "location",
            "weekly_capacity",
            "portfolio_website",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "hourly_rate": forms.NumberInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": "4"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "weekly_capacity": forms.NumberInput(attrs={"class": "form-control"}),
            "portfolio_website": forms.URLInput(attrs={"class": "form-control"}),
        }
