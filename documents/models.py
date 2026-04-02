from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (v{self.version})"


class DocumentChange(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='changes')
    original_text = models.TextField()
    replacement_text = models.TextField()
    position = models.PositiveIntegerField()
    version_at_change = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'"{self.original_text}" → "{self.replacement_text}" at pos {self.position}'
