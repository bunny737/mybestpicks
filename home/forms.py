from django import forms


class EmailSignupForm(forms.Form):
    email = forms.EmailField(label="Email address", max_length=254)
    consent = forms.BooleanField(
        label="I agree to receive occasional emails and have read the privacy notice.",
        error_messages={"required": "Please confirm you agree to receive emails."},
    )
