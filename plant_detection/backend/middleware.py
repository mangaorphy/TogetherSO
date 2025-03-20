from django.shortcuts import redirect
import datetime

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for login and registration pages
        if request.path.startswith('/admin/') or request.path == '/login/' or request.path == '/register/':
            return self.get_response(request)

        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Get the last activity timestamp from the session
            last_activity = request.session.get('last_activity')

            # If no activity timestamp exists, set it now
            if not last_activity:
                request.session['last_activity'] = datetime.datetime.now().timestamp()
                return self.get_response(request)

            # Calculate the time elapsed since the last activity
            time_since_last_activity = datetime.datetime.now().timestamp() - last_activity

            # If more than 2 hours have passed, log the user out
            if time_since_last_activity > 7200:  # 2 hours in seconds
                from django.contrib.auth import logout
                logout(request)
                return redirect('login')  # Redirect to the login page

            # Update the last activity timestamp
            request.session['last_activity'] = datetime.datetime.now().timestamp()

        return self.get_response(request)