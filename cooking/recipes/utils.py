import json
import requests
import zeep

from schema import Schema, And, Use

from django.conf import settings
from django.http import JsonResponse

from .models import Ingredient, Recipe


def serialize_recipe(recipe):
    categories = read_json('RecipesSearchEngine/categorie_preprocessed.json')
    if type(recipe) is dict:
        return {
            "id": recipe["id"],
            "name": recipe["name"],
            "image_url": recipe["image_url"],
            "ingredients": recipe["ingredients.unstructured_data"],
            "instructions": recipe["instructions"].split('\n'),
            "duration": recipe["duration"][0],
            "categories": [categories[recipe["category"]]],
            "servings": recipe["servings"][0],
            "rating": recipe["rating"][0],
            "user": recipe["user"],
        }
    return {
        "id": recipe.id,
        "name": recipe.name,
        "image_url": recipe.image_url,
        "ingredients": [i.unstructured_data for i in recipe.ingredients.all()],
        "instructions": recipe.instructions.split('\n'),
        "duration": recipe.duration,
        "categories": [recipe.category],
        "servings": recipe.servings,
        "rating": recipe.rating,
        "user": recipe.user
    }


def read_json(json_file_name):
    """ Reads the json data and saves it in data """
    data = []
    print("Reading the recipe data from the JSON file ...")
    with open(json_file_name, 'r', encoding="utf-8") as json_data:
        data = json.load(json_data)

    print("  Found {} recipes \n".format(len(data)))
    return data


def fill_in_db_from_json(filename):
    return create_recipe_from_json(read_json(filename))


def create_recipe_from_json(data):

    recipe_schema = Schema({
        'name': And(str, len),
        'user': And(str, len),
        'url': And(Use(str), lambda url: 'http' in url),
        'category': And(str, len),
        'servings': And(str, len),
        'comments': Schema([str]),
        'instructions': And(str, len),
        'image_url': And(str, lambda url: 'http' in url),
        'duration': And(str, len),
        'rating': And(str, len),
        'difficulty': And(str, len)
    })

    ingredients_schema = Schema([{
        'name': And(str, len),
        'unit': And(str, len),
        'quantity': And(str, len),
        'unstructured_data': And(str, len)
    }])

    counter = 0
    for rec in data:
        try:
            ingr = rec.pop('ingredients', {})
            rec.pop('duration_bound', None)

            # validate the schema for ingredients and recipes
            ingr_data = ingredients_schema.validate(ingr)
            rec_data = recipe_schema.validate(rec)

            # don't create new recipe with duplicate name
            if Recipe.objects.filter(name__icontains=rec_data['name']).exists():
                continue

            recipe = Recipe.objects.create(**rec)

            for ingredient in ingr_data:
                try:
                    ingredient.pop('common', None)
                    recipe.ingredients.add(Ingredient.objects.create(**ingredient))
                except Exception as exc:
                    print(ingredient)
                    print(rec)
                    print(exc)
                    continue

            counter += 1
        except Exception as e:
            print(e)

    return counter > 0


def get_default_response():
    return JsonResponse({
        "recipes": [serialize_recipe(r) for r in Recipe.objects.all()[:100]]
    })


def start_soap_crawler(wsdl=settings.SOAP_WSDL, website_name='KulinarBg', recipes_count=5):
    client = zeep.Client(wsdl=settings.SOAP_WSDL)
    client.service.StartCrawler(website_name, recipes_count)


def save_rest_json_recipes(url):
    recipes = requests.get(url).json()
    return create_recipe_from_json(json.loads(recipes))


def save_soap_json_recipes():
    pass
