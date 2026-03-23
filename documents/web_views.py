from django.shortcuts import render, get_object_or_404
from .models import Document


def home(request):
    documents = Document.objects.order_by('-created_at')
    return render(request, 'documents/home.html', {'documents': documents})


def create_document(request):
    return render(request, 'documents/create.html')


def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'documents/detail.html', {'document': document})


def update_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'documents/update.html', {'document': document})


def search_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'documents/search.html', {'document': document})


def cross_search(request):
    return render(request, 'documents/cross_search.html')
