from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=5)
    quantity = models.CharField(max_length=10)
    unstructured_data = models.TextField()

    def __str__(self):
        return self.unstructured_data


class Recipe(models.Model):
    name = models.CharField(max_length=300)
    user = models.CharField(max_length=100)
    url = models.URLField()
    category = models.CharField(max_length=100)
    servings = models.SmallIntegerField()
    comments = models.TextField()
    instructions = models.TextField()
    image_url = models.URLField()
    duration = models.CharField(max_length=10)
    rating = models.CharField(max_length=10)
    difficulty = models.CharField(max_length=10)
    ingredients = models.ManyToManyField(Ingredient, related_name='ingredients')

    def __str__(self):
        return self.name
