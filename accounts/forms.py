import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Category, ClientProfile, FreelancerProfile, Skill


User = get_user_model()


class LoginForm(AuthenticationForm):
    """Логін по email (USERNAME_FIELD = 'email')"""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "placeholder": "Email",
            "class": "login-input"
        })
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password",
            "class": "login-input"
        })
    )


class ClientRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "example@example.com"})
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "John"})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "Smith"})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput()
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput()
    )
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"})
    )
    company_name = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput()
    )
    location = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput()
    )

    class Meta:
        model = User
        fields = ("email", "password1", "password2", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                continue
            field.widget.attrs.setdefault("class", "")
            field.widget.attrs["class"] += " form-control"


    def clean_location(self):
        location = (self.cleaned_data.get("location") or "").strip()
        if location and not re.match(r"^[A-Za-z .'-]+,\s?[A-Z]{2}$", location):
            raise forms.ValidationError("Use format like: Kyiv, UA")
        return location

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "client"
        if commit:
            user.save()
            user.category.set(self.cleaned_data.get("category") or [])
            ClientProfile.objects.create(
                user=user,
                company_name=self.cleaned_data.get("company_name", ""),
                location=self.cleaned_data.get("location", ""),
                is_open_to_agencies=True,
                hire_rate=0,
            )
        return user


class FreelancerRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "example@example.com"})
    )
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "John"})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "Smith"})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput()
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput()
    )
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"})
    )
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Backend Developer"})
    )
    hourly_rate = forms.IntegerField(
        widget=forms.NumberInput()
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"placeholder": "Short bio", "rows": 3})
    )
    portfolio_website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={"placeholder": "https://example.com"})
    )
    portfolio_file = forms.FileField(required=False)
    location = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput()
    )
    weekly_capacity = forms.TypedChoiceField(
        choices=[(str(value), f"{value} hrs") for value in range(20, 71, 5)],
        coerce=int,
        empty_value=None,
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False
    )
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"})
    )
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ("email", "password1", "password2", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                continue
            field.widget.attrs.setdefault("class", "")
            if "form-select" not in field.widget.attrs["class"]:
                field.widget.attrs["class"] += " form-control"

    def clean(self):
        cleaned_data = super().clean()
        has_link = bool(cleaned_data.get("portfolio_website"))
        has_file = bool(cleaned_data.get("portfolio_file"))
        if has_link and has_file:
            self.add_error("portfolio_website", "Choose either a portfolio link or a file, not both.")
            self.add_error("portfolio_file", "Choose either a portfolio link or a file, not both.")
        if not has_link and not has_file:
            self.add_error("portfolio_website", "Provide a portfolio link or upload a file.")
            self.add_error("portfolio_file", "Provide a portfolio link or upload a file.")
        return cleaned_data

    def clean_location(self):
        location = (self.cleaned_data.get("location") or "").strip()
        if location and not re.match(r"^[A-Za-z .'-]+,\s?[A-Z]{2}$", location):
            raise forms.ValidationError("Use format like: Kyiv, UA")
        return location

    def clean_weekly_capacity(self):
        value = self.cleaned_data.get("weekly_capacity")
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "freelancer"
        if commit:
            user.save()
            user.category.set(self.cleaned_data.get("category") or [])
            profile = FreelancerProfile.objects.create(
                user=user,
                title=self.cleaned_data.get("title", ""),
                hourly_rate=self.cleaned_data.get("hourly_rate") or 0,
                bio=self.cleaned_data.get("bio", ""),
                portfolio_website=self.cleaned_data.get("portfolio_website", ""),
                portfolio_file=self.cleaned_data.get("portfolio_file"),
                location=self.cleaned_data.get("location") or "Not provided",
                weekly_capacity=self.cleaned_data.get("weekly_capacity") or 40,
                avatar=self.cleaned_data.get("avatar"),
            )
            profile.skills.set(self.cleaned_data.get("skills") or [])
        return user
