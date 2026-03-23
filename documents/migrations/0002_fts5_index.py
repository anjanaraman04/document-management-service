from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    content,
                    content='documents_document',
                    content_rowid='id'
                );

                INSERT INTO documents_fts(rowid, content)
                SELECT id, content FROM documents_document;
            """,
            reverse_sql="DROP TABLE IF EXISTS documents_fts;",
        ),
    ]
