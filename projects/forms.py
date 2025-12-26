from django import forms

from .models import Application


class ApplicationForm(forms.ModelForm):
    portfolio_format = forms.ChoiceField(
        choices=[
            ("link", "Link"),
            ("file", "File"),
        ],
        widget=forms.RadioSelect,
        initial="link",
        required=True,
    )

    class Meta:
        model = Application
        fields = [
            "full_name",
            "email",
            "pitch",
            "portfolio_url",
            "portfolio_file",
            "availability",
            "estimated_timeline",
            "proposed_budget",
            "additional_notes",
        ]

        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Alex Morgan",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "alex@email.com",
            }),
            "pitch": forms.Textarea(attrs={
                "class": "form-control",
                "rows": "4",
            }),
            "portfolio_url": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://portfolio.com"}),
            "portfolio_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "availability": forms.Select(attrs={"class": "form-select"}),
            "estimated_timeline": forms.TextInput(attrs={"class": "form-control"}),
            "proposed_budget": forms.TextInput(attrs={"class": "form-control", "placeholder": "$2,500"}),
            "additional_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": "3",
                "placeholder": "Optional notes, questions, or milestones.",
            }),
        }

    def clean(self):
        cleaned = super().clean()
        fmt = cleaned.get("portfolio_format")
        link = cleaned.get("portfolio_url")
        file = cleaned.get("portfolio_file")

        if fmt == "link":
            if not link:
                self.add_error("portfolio_url", "Portfolio link is required.")
            cleaned["portfolio_file"] = None
        elif fmt == "file":
            if not file:
                self.add_error("portfolio_file", "Portfolio file is required.")
            cleaned["portfolio_url"] = None

        return cleaned
