from django.shortcuts import render
from django.http import JsonResponse
from RecipesSearchEngine.RecipesSearchEngine import generate_search_suggestions, complex_search

SOLR_URL = "http://localhost:8983/solr"
JSON_FILENAME = "scrapy_crawler/scrapy_crawler/recipes.json"
# json_file_name = "recipes_500_refined_edited.json"
COLLECTION = "recipes_search_engine"


def get_recipes_by_keyword(request, *args, **kwargs):
    # TODO: escape * and other symbols
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "name")
    recipes = generate_search_suggestions(
        SOLR_URL, COLLECTION, keyword, search_field)
    return JsonResponse({"recipes": recipes})


def get_complex_search_results(request, *args, **kwargs):
    # TODO: escape * and other symbols
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "name")
    categories = request.GET.getlist("categories", None)
    duration_range = request.GET.getlist("duration_range", (0, 100))
    keys = ["category", "user_str", "duration"]
    facet_input = {
        "category": categories,
        "user_str": keyword,
        "duration": duration_range
    }
    facet_fields = request.GET.getlist("fields", keys)
    facet_input = {}
    recipes = complex_search(
        SOLR_URL, COLLECTION, keyword, search_field,
        facet_fields, facet_input, duration_range
    )
    return JsonResponse({"recipes": recipes})
