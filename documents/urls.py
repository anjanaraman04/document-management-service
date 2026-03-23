from django.urls import path
from .views import DocumentCreateView, DocumentDetailView, DocumentCrossSearchView, DocumentSearchView, DocumentReplaceTextView

urlpatterns = [
    path('', DocumentCreateView.as_view(), name='document-create'),
    path('search/', DocumentCrossSearchView.as_view(), name='document-cross-search'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<int:pk>/search/', DocumentSearchView.as_view(), name='document-search'),
    path('<int:pk>/replace-text/', DocumentReplaceTextView.as_view(), name='document-replace-text'),
]
