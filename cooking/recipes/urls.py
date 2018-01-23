"""cooking URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path
from .views import (
    get_recipes_by_keyword, get_complex_search_results, home,
    search_recipes_by_keyword, search_recipes_by_category)


urlpatterns = [
    path('home/', home, name='home'),
    path('base-search/', get_recipes_by_keyword, name='base-search'),
    path('search/', get_recipes_by_keyword, name='search'),
    path('search1/', search_recipes_by_keyword, name='search'),
    path('category-search/', search_recipes_by_category, name='category-search'),
    path('complex-search/', get_complex_search_results, name='complex-search'),
]
