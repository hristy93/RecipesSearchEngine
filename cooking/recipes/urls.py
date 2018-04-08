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
    search_recipes_by_keyword, search_recipes_by_category, get_relevant_recipes,
    get_recipe_details, get_recipes, get_categories, get_users,
    get_rest_recipes, get_soap_recipes)


urlpatterns = [
    path('home/', home, name='home'),
    path('search-suggestor/', get_recipes_by_keyword, name='search-suggestor'),
    path('base-search/', search_recipes_by_keyword, name='base-search'),
    path('category-search/', search_recipes_by_category, name='category-search'),
    path('complex-search/', get_complex_search_results, name='complex-search'),
    path('relevant-search/', get_relevant_recipes, name='relevant-search'),
    path('details/<int:id>/', get_recipe_details, name='details'),
    path('all-recipes/', get_recipes, name='all-recipes'),
    path('all-categories/', get_categories, name='all-categories'),
    path('all-users/', get_users, name='all-users'),

    path('rest-recipes/', get_rest_recipes, name='rest-recipes'),
    path('soap-recipes/', get_soap_recipes, name='soap-recipes'),
]
