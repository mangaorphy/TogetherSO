# accounts/views.py
from django.shortcuts import render
from django.views.generic import CreateView, TemplateView, RedirectView
from django.contrib.auth import login,logout
from django.contrib.auth.views import LoginView
from django.contrib.auth import get_user_model
User = get_user_model()  

from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str # force_text on older versions of Django

from .forms import SignUpForm, token_generator

class SignUpView(CreateView):
    form_class = SignUpForm 
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('check_email')

    def form_valid(self, form):
        to_return = super().form_valid(form)
        
        user = form.save()
        user.is_active = False # Turns the user status to inactive
        user.save()

        form.send_activation_email(self.request, user)

        return to_return

class ActivateView(RedirectView):
    url = reverse_lazy('success')

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)  # Corrected from user_model to User
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            return super().get(request, uidb64, token)
        else:
            return render(request, 'accounts/activate_account_invalid.html')
        
class CheckEmailView(TemplateView):
    template_name = 'accounts/check_email.html'

class SuccessView(TemplateView):
    template_name = 'accounts/success.html'

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

# class CustomLoginView(LoginView):
#     template_name = 'account/login.html'

#     def dispatch(self, request, *args, **kwargs):
#         if request.user.is_authenticated:
#             return redirect('dashboard')  # Redirect authenticated accounts to the dashboard
#         return super().dispatch(request, *args, **kwargs)
    

from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    """
    Custom logout view for TogetherSO.
    """
    logout(request)  # Log the user out
    return redirect('welcome')  # Redirect to the welcome page

# accounts/views.py

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def custom_login_view(request):
    """
    Custom login view for TogetherSO.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect authenticated users to the dashboard

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)

            # Get the 'next' parameter from POST or GET
            next_url = request.POST.get('next', '') or request.GET.get('next', '')

            # Default to 'dashboard' if 'next' is empty or invalid
            if not next_url:
                next_url = reverse_lazy('dashboard')

            return redirect(next_url)  # Redirect to the intended page
        else:
            messages.error(request, 'Invalid credentials or account not activated.')
            return redirect('login')  # Redirect back to login page with error message

    return render(request, 'accounts/login.html')  # Use the accounts login template

def register(request):
    """
    Custom registration view for TogetherSO.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Validate passwords match
        if password != confirm_password:
            return render(request, "accounts/register.html", {"error": "Passwords do not match"})

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, "accounts/register.html", {"error": "Username already taken"})

        # Create the user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_active = False  # Deactivate the account until confirmed
            user.save()

            # Send activation email
            form = SignUpForm({"username": username, "email": email})
            form.send_activation_email(request, user)

            return redirect("check_email")  # Redirect to check email page
        except Exception as e:
            messages.error(request, f"Error creating account: {e}")
            return redirect("register")

    return render(request, "accounts/register.html")

def welcome_view(request):
    """
    Django view for rendering the welcome page.
    If the user is already authenticated, redirect to the dashboard.
    """
    if request.user.is_authenticated:
        return redirect('home')  # Redirect authenticated accounts to the home

    return render(request, 'accounts/welcome.html')

def resend_activation(request):
    """
    Resends the activation email to the user.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                messages.warning(request, "This account is already activated.")
                return redirect("login")
            form = SignUpForm({"username": user.username, "email": user.email})
            form.send_activation_email(request, user)
            messages.success(request, "Activation email resent successfully!")
        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
        return redirect("check_email")
    return render(request, "accounts/resend_activation.html")
