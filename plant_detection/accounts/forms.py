from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from .token import token_generator

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text="Required. Enter a valid email address.",
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False  # User remains inactive until email verification
        if commit:
            user.save()
        return user

    def send_activation_email(self, request, user):
        current_site = request.get_host()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        
        subject = 'Activate Your TogetherSO Account'
        message = render_to_string('accounts/activate_account.html', {
            'user': user,
            'domain': current_site,
            'uid': uid,
            'token': token,
            'protocol': 'https' if request.is_secure() else 'http'
        })
        
        # Use EmailMessage for better control
        email = EmailMessage(
            subject,
            message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        email.content_subtype = "html"  # Enable HTML content
        email.send(fail_silently=False)