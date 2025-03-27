

from django.apps import AppConfig
import os

class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'

    # def ready(self):
    #     """
    #     Loads the AI model and disease info when the app starts.
    #     """
    #     if os.environ.get('RUN_MAIN') == 'true':  # Prevent double execution during startup
    #         from .views import load_model
    #         load_model()
