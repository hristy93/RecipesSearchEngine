# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.shortcuts import render
from RecipesSearchEngine.RecipesSearchEngine import (
    generate_search_suggestions, complex_search)
from .utils import serialize_recipe
from .models import Recipe


SOLR_URL = "http://localhost:8983/solr"
JSON_FILENAME = "scrapy_crawler/scrapy_crawler/recipes.json"
# json_file_name = "recipes_500_refined_edited.json"
COLLECTION = "recipes_search_engine"


def get_recipes_by_keyword(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not request.GET:
        return JsonResponse({"recipes": []})
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "name")
    recipes = generate_search_suggestions(
        SOLR_URL, COLLECTION, keyword, search_field)
    return JsonResponse({"recipes": recipes})


def get_complex_search_results(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not request.GET:
        return JsonResponse({"recipes": []})
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "ingredients.name")
    categories = request.GET.getlist("categories", ["осн"])
    duration_range = request.GET.getlist("duration", (0, 100))
    keys = ["category", "user_str", "duration"]
    facet_input = {
        "category": categories,
        "user_str": None,
        "duration": duration_range
    }
    facet_fields = request.GET.getlist("fields", keys)
    recipes, suggested_search_query_words, suggested_search_queries = complex_search(
        SOLR_URL, COLLECTION, keyword, search_field,
        facet_fields, facet_input, duration_range
    )
    return JsonResponse({
        "recipes": [serialize_recipe(r) for r in recipes],
        # "recipes": recipes,
        "suggested_words": suggested_search_query_words,
        "suggested_queries": suggested_search_queries
    })


def home(request, *args, **kwargs):
    recipes = Recipe.objects.all()
    return render(request, "index.html", {
        "recipes": [serialize_recipe(r) for r in recipes]
    })
