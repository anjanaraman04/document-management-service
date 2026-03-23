from django.db import connection
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import Document


@receiver(pre_save, sender=Document)
def capture_old_content(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_content = Document.objects.get(pk=instance.pk).content
        except Document.DoesNotExist:
            instance._old_content = None
    else:
        instance._old_content = None


@receiver(post_save, sender=Document)
def update_fts_index(sender, instance, created, **kwargs):
    with connection.cursor() as cursor:
        if created:
            cursor.execute(
                "INSERT INTO documents_fts(rowid, content) VALUES (%s, %s)",
                [instance.pk, instance.content],
            )
        else:
            old_content = getattr(instance, '_old_content', None)
            if old_content is not None:
                cursor.execute(
                    "INSERT INTO documents_fts(documents_fts, rowid, content) VALUES ('delete', %s, %s)",
                    [instance.pk, old_content],
                )
            cursor.execute(
                "INSERT INTO documents_fts(rowid, content) VALUES (%s, %s)",
                [instance.pk, instance.content],
            )


@receiver(post_delete, sender=Document)
def delete_fts_index(sender, instance, **kwargs):
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO documents_fts(documents_fts, rowid, content) VALUES ('delete', %s, %s)",
            [instance.pk, instance.content],
        )
