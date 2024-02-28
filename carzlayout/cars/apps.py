from django.apps import AppConfig


# register(User, app=__package__)
class CarsConfig(AppConfig):
    verbose_name = "Таблицы для расчета расстановки машин"
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cars'

    def ready(self):
        from django.contrib.auth.models import User
        from simple_history import register
        register(User)