import json
from .models import Ingredient, Recipe


def serialize_recipe(recipe):
    if type(recipe) is dict:
        return {
            "id": recipe["id"],
            "name": recipe["name"],
            "image_url": recipe["image_url"],
            "ingredients": recipe["ingredients.unstructured_data"],
            "instructions": recipe["instructions"],
            "duration": recipe["duration"][0],
            "categories": recipe["category_str"],
            "servings": recipe["servings"][0],
            "rating": recipe["rating"][0],
        }
    return {
        "id": recipe.id,
        "name": recipe.name,
        "image_url": recipe.image_url,
        "ingredients": [i.unstructured_data for i in recipe.ingredients.all()],
        "instructions": recipe.instructions,
        "duration": recipe.duration,
        "categories": [recipe.category],
        "servings": recipe.servings,
        "rating": recipe.rating,
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
    data = read_json(filename)
    for rec in data:
        e = rec.pop('ingredients', [])
        r = Recipe.objects.create(**rec)
        for i in e:
            r.ingredients.add(Ingredient.objects.create(**i))
