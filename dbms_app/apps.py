from django.apps import AppConfig


class DbmsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dbms_app'

    def ready(self):
        # Importing signals registers the MongoEngine post_save / pre_delete
        # handlers that act as our database "triggers".
        from . import signals  # noqa: F401
