# -*- coding: utf-8 -*-
import json
import logging
import operator
import requests
import sys
import zeep

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from RecipesSearchEngine.bulgarian_stemmer.bulstem import stem
from RecipesSearchEngine.RecipesSearchEngine import (
    generate_search_suggestions, complex_search, solr_search_recipes_by_category,
    solr_single_term_search_by_field, solr_facet_search_recipe_category_by_field,
    more_like_this_recipe)
from .utils import serialize_recipe, read_json, get_default_response, create_recipe_from_json
from .models import Recipe


SOLR_URL = "http://localhost:8983/solr"
JSON_FILENAME = "scrapy_crawler/scrapy_crawler/recipes.json"
# json_file_name = "recipes_500_refined_edited.json"
COLLECTION = "recipes_search_engine"


def enable_win_unicode_console():
    try:
        # Fix UTF8 output issues on Windows console.
        # Does nothing if package is not installed
        from win_unicode_console import enable
        enable()
    except ImportError:
        pass


# enables the unicode console encoding on Windows
if sys.platform == "win32":
    enable_win_unicode_console()



def get_recipes_by_keyword(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not(request.GET and request.GET.get("keyword")):
        return get_default_response()
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "name")
    found, titles = generate_search_suggestions(
        SOLR_URL, COLLECTION, keyword, search_field)
    recipes = Recipe.objects.filter(name__in=titles)
    recipes = sorted(recipes, key=lambda x: titles.index(x.name))
    recipes = [serialize_recipe(r) for r in recipes]
    return JsonResponse({
        "recipes": recipes,
    })


def search_recipes_by_keyword(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not(request.GET and request.GET.get("keyword")):
        return get_default_response()
    keyword = request.GET.get("keyword")
    search_field = request.GET.get("field", "name")
    titles = solr_single_term_search_by_field(
        SOLR_URL, COLLECTION, keyword, search_field)
    recipes = Recipe.objects.filter(name__in=titles)
    recipes = sorted(recipes, key=lambda x: titles.index(x.name))
    return JsonResponse({"recipes": [serialize_recipe(r) for r in recipes]})


def get_complex_search_results(request, *args, **kwargs):
    # TODO: escape * and other symbols
    if not request.GET:
        return JsonResponse({"recipes": []})
    keyword = request.GET.get("keyword")
    categories = request.GET.getlist("category")
    duration_range = request.GET.getlist("duration[]", (0, 500))
    user = request.GET.get("user")
    is_ingredient = request.GET.get("is_ingredient", 'false') == 'true'
    search_field = "ingredients.name"if is_ingredient else "name"

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
    titles = [t['name'] for t in recipes]
    recipes = Recipe.objects.filter(name__in=titles)
    recipes = sorted(recipes, key=lambda x: titles.index(x.name))
    suggested_search_query_words.pop('or', None)
    return JsonResponse({
        "recipes": [serialize_recipe(r) for r in recipes],
        # "suggested_words": suggested_search_query_words.get(keyword, []),
        "suggested_words": suggested_search_query_words,
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
        "suggested_words": {},
        "suggested_queries": []
    })


def get_recipes(request):
    all_recipes = Recipe.objects.all()[:500]
    recipes = [serialize_recipe(r) for r in all_recipes]
    return JsonResponse({"recipes": recipes})


def get_categories(request):
    categories = read_json('RecipesSearchEngine/categorie_preprocessed.json')
    return JsonResponse({
        "categories": sorted(categories.values())
    })


def get_users(request):
    users = list(set(Recipe.objects.values_list('user', flat=True)))
    return JsonResponse({
        "users": sorted(users)
    })


def get_rest_recipes(request):
    url = 'http://localhost:9000/some-endpoint'
    recipes = requests.get(url).json()

    result = create_recipe_from_json(recipes)
    message = 'Success' if result else 'Failure'

    return JsonResponse({'message': message})


def start_soap_crawler(request):
    wsdl = 'http://localhost:61609/Service.svc?singleWsdl'
    client = zeep.Client(wsdl=wsdl)
    website_name = 'KulinarBg'
    recipes_count = 5
    # element = client.get_element('ns0:ElementName')
    # obj = element(_value_1={'item_1_a': 'foo', 'item_1_b': 'bar'})
    recipes = client.service.StartCrawler(website_name, recipes_count)

    result = create_recipe_from_json(recipes)
    message = 'Success' if result else 'Failure'

    return JsonResponse({'message': message})


def get_soap_recipes(request):
    wsdl = 'http://localhost:61609/Service.svc?singleWsdl'
    client = zeep.Client(wsdl=wsdl)
    website_name = 'KulinarBg'
    recipes_count = 5
    # element = client.get_element('ns0:ElementName')
    # obj = element(_value_1={'item_1_a': 'foo', 'item_1_b': 'bar'})
    recipes = client.service.GetRecipeData(recipes_count)
    # print(recipes)
    result = create_recipe_from_json(json.loads(recipes))
    message = 'Success' if result else 'Failure'

    return JsonResponse({'message': message})


def get_soap_recipes1(request):
    wsdl = 'http://localhost:61328/soap11'
    client = zeep.Client(wsdl=wsdl)
    website_name = 'KulinarBg'
    recipes_count = 5
    hello_type = client.get_type('ns1:hello')
    hello = hello_type(name='website_name')
    # recipes = client.service.hello(hello)
    # log = logging.getLogger(__name__)
    # for service in client.wsdl.services.values():
        # for port in service.ports.values():
            # operations = sorted(
            # port.binding._operations.values(),
            # key=operator.attrgetter('name'))
            # for operation in operations:
               # print('operation name: ' + str(operation.name))
    recipes = client.service.hello(hello = {'name': '3'})

    print(recipes)
    message = 'Success' if result else 'Failure'

    return JsonResponse({'message': message})


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
        SOLR_URL, COLLECTION, search_input, category, results_count=9)
    titles = [t['name'] for t in recipes]
    recipes = Recipe.objects.filter(name__in=titles)
    recipes = sorted(recipes, key=lambda x: titles.index(x.name))
    return render(request, "details.html", {
        "recipe": serialize_recipe(recipe),
        "recipes": [serialize_recipe(r) for r in recipes],
        "categories": [],
        "difficulties": [],
        "users": [],
        "suggested_words": {},
        "suggested_queries": []
    })
