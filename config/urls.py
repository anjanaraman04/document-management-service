"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from documents.web_views import home, create_document, document_detail, update_document, search_document, cross_search

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/documents/', include('documents.urls')),
    path('', home, name='home'),
    path('new/', create_document, name='create-document'),
    path('documents/<int:pk>/', document_detail, name='document-detail'),
    path('documents/<int:pk>/edit/', update_document, name='update-document'),
    path('documents/<int:pk>/search/', search_document, name='search-document'),
    path('search/', cross_search, name='cross-search'),
]
