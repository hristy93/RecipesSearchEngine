def serialize_recipe(recipe):
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
