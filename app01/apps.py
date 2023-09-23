from django.apps import AppConfig

print("apps running")

class App01Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app01'
