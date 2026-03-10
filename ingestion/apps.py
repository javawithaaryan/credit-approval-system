from django.apps import AppConfig
from django.db.models.signals import post_migrate


def trigger_ingestion(sender, **kwargs):
    """Trigger data ingestion task after migrations complete."""
    from ingestion.tasks import ingest_data
    ingest_data.delay()


class IngestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ingestion'

    def ready(self):
        post_migrate.connect(trigger_ingestion, sender=self)
