from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "placeholder": "Email",
        })
    )

    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            "placeholder": "Name",
        })
    )

    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            "placeholder": "Surname",
        })
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password",
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Repeat password",
        })
    )

    role = forms.ChoiceField(
        choices=(("client", "Client"), ("freelancer", "Freelancer")),
        widget=forms.Select(attrs={"class": "login-input"}),
        label="You are"
    )

    class Meta:
        model = User
        fields = ("email", "password1", "password2", "first_name", "last_name", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "")
            field.widget.attrs["class"] += " login-input"


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
