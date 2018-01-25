# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from bulgarian_stemmer.bulstem import stem
from RecipesSearchEngine.RecipesSearchEngine import (
    generate_search_suggestions, complex_search, solr_search_recipes_by_category,
    solr_single_term_search_by_field, solr_facet_search_recipe_category_by_field,
    more_like_this_recipe)
from .utils import serialize_recipe, read_json
from .models import Recipe


SOLR_URL = "http://localhost:8983/solr"
JSON_FILENAME = "scrapy_crawler/scrapy_crawler/recipes.json"
# json_file_name = "recipes_500_refined_edited.json"
COLLECTION = "recipes_search_engine"


# old
def get_recipes_by_keyword(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not request.GET:
        return JsonResponse({"recipes": []})
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "name")
    found, titles = generate_search_suggestions(
        SOLR_URL, COLLECTION, keyword, search_field)
    recipes = Recipe.objects.filter(name__in=titles)
    recipes = [serialize_recipe(r) for r in recipes]
    return JsonResponse({
        "recipes": recipes,
    })


def search_recipes_by_keyword(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not request.GET:
        return JsonResponse({"recipes": []})
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "name")
    titles = solr_single_term_search_by_field(
        SOLR_URL, COLLECTION, keyword, search_field)
    recipes = Recipe.objects.filter(name__in=titles)
    return JsonResponse({"recipes": [serialize_recipe(r) for r in recipes]})


def get_complex_search_results(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not request.GET:
        return JsonResponse({"recipes": []})
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "name")
    categories = request.GET.getlist("category")
    duration_range = request.GET.getlist("duration[]", (0, 500))
    user = request.GET.get("user")

    facet_input = {}
    if categories:
        facet_input["category"] = [stem(c) for c in categories]
    if duration_range:
        facet_input["duration"] = duration_range
    if user:
        facet_input["user_str"] = [user]

    # facet_input = {
    #     "category": categories,
    #     "user_str": user,
    #     "duration": duration_range
    # }

    keys = ["category", "user_str", "duration"]
    facet_fields = request.GET.getlist("fields", keys)
    recipes, suggested_search_query_words, suggested_search_queries = complex_search(
        SOLR_URL, COLLECTION, keyword, search_field,
        facet_fields, facet_input, duration_range
    )
    recipes = Recipe.objects.filter(name__in=[t['name'] for t in recipes])
    return JsonResponse({
        "recipes": [serialize_recipe(r) for r in recipes],
        "suggested_words": suggested_search_query_words.get(keyword, []),
        "suggested_queries": suggested_search_queries
    })


def search_recipes_by_category(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not (request.GET or request.GET.get("category")):
        return JsonResponse({"recipes": []})
    keyword = stem(request.GET.get("category"))
    titles = solr_search_recipes_by_category(
        SOLR_URL, COLLECTION, keyword)
    recipes = Recipe.objects.filter(name__in=titles)[:100]
    return JsonResponse({"recipes": [serialize_recipe(r) for r in recipes]})


def home(request, *args, **kwargs):
    all_recipes = Recipe.objects.all()
    difficulties = list(set(all_recipes.values_list('difficulty', flat=True)))
    users = list(set(all_recipes.values_list('user', flat=True)))
    recipes = [serialize_recipe(r) for r in all_recipes[:100]]
    # categories = solr_facet_search_recipe_category_by_field(
    #     SOLR_URL, COLLECTION, "", [])
    categories = read_json('RecipesSearchEngine/categorie_preprocessed.json')
    return render(request, "index.html", {
        "recipes": recipes,
        # "categories": sorted(list(categories['category_str'].keys())),
        "categories": sorted(categories.values()),
        "difficulties": sorted(difficulties),
        "users": sorted(users),
        "suggested_words": []
    })


# not used anymore
def get_relevant_recipes(request, *args, **kwargs):
    if not request.GET:
        return JsonResponse({"recipes": []})
    search_input = request.GET.get("name")
    category = request.GET.get("category")
    if not (search_input or category):
        return JsonResponse({"recipes": []})
    recipes = more_like_this_recipe(
        SOLR_URL, COLLECTION, search_input, stem(category))
    return JsonResponse({"recipes": [serialize_recipe(r) for r in recipes]})


def get_recipe_details(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    search_input = recipe.name
    category = stem(recipe.category)
    recipes = more_like_this_recipe(
        SOLR_URL, COLLECTION, search_input, category, results_count=6)
    recipes = Recipe.objects.filter(name__in=[t['name'] for t in recipes])
    return render(request, "details.html", {
        "recipe": serialize_recipe(recipe),
        "recipes": [serialize_recipe(r) for r in recipes],
        "categories": [],
        "difficulties": [],
        "users": [],
        "suggested_words": []
    })
