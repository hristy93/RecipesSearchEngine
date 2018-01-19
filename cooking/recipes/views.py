from django.shortcuts import render
from django.http import JsonResponse
from RecipesSearchEngine.RecipesSearchEngine import generate_search_suggestions

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
