import json
from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Document


@method_decorator(csrf_exempt, name='dispatch')
class DocumentCreateView(View):
    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        title = body.get('title')
        content = body.get('content')

        if not title or not content:
            return JsonResponse({'error': 'Both "title" and "content" fields are required'}, status=400)

        document = Document.objects.create(
            title=title,
            content=content,
        )

        return JsonResponse({
            'id': document.pk,
            'title': document.title,
            'content': document.content,
            'version': document.version,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentDetailView(View):
    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        return JsonResponse({
            'id': document.pk,
            'title': document.title,
            'content': document.content,
            'version': document.version,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
        })


def extract_snippet(content, query, padding=50):
    index = content.lower().find(query.lower())
    if index == -1:
        return None
    start = max(0, index - padding)
    end = min(len(content), index + len(query) + padding)
    snippet = content[start:end]
    # Wrap the matched term with markers for highlight rendering
    match = content[index:index + len(query)]
    snippet = snippet.replace(match, f'>>>{match}<<<', 1)
    return snippet


@method_decorator(csrf_exempt, name='dispatch')
class DocumentCrossSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'error': 'Query parameter "q" is required'}, status=400)

        documents = Document.objects.filter(content__icontains=query)

        if not documents.exists():
            return JsonResponse({'error': f'"{query}" not found in any document'}, status=404)

        results = [
            {'id': doc.pk, 'snippet': extract_snippet(doc.content, query)}
            for doc in documents
        ]

        return JsonResponse({'query': query, 'results': results})


@method_decorator(csrf_exempt, name='dispatch')
class DocumentSearchView(View):
    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'error': 'Query parameter "q" is required'}, status=400)

        snippet = extract_snippet(document.content, query)

        if snippet is None:
            return JsonResponse({'error': f'"{query}" not found in document'}, status=404)

        return JsonResponse({
            'id': document.pk,
            'query': query,
            'snippet': snippet,
        })


@method_decorator(csrf_exempt, name='dispatch')
class DocumentReplaceTextView(View):
    def patch(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        changes = body.get('changes')

        if not changes:
            return JsonResponse({'error': '"changes" array is required'}, status=400)

        if not isinstance(changes, list):
            return JsonResponse({'error': '"changes" must be an array'}, status=400)

        warnings = []
        seen_search_terms = set()

        for i, change in enumerate(changes):
            # Validate structure
            if not isinstance(change, dict) or 'search' not in change or 'replacement' not in change:
                warnings.append(f'Change at index {i} is missing "search" or "replacement" fields — skipped')
                continue

            search = change['search']
            replacement = change['replacement']

            # Check for duplicate search terms
            if search in seen_search_terms:
                warnings.append(f'Duplicate search term "{search}" at index {i} — skipped')
                continue

            seen_search_terms.add(search)

            # Check search term exists in current content
            if search not in document.content:
                warnings.append(f'Search term "{search}" not found in document — skipped')
                continue

            document.content = document.content.replace(search, replacement)

        document.version += 1
        document.save()

        return JsonResponse({
            'id': document.pk,
            'title': document.title,
            'content': document.content,
            'version': document.version,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
            'warnings': warnings,
        })
