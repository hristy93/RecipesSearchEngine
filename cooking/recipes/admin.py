from django.contrib import admin
from .models import Ingredient, Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    filter_horizontal = ('ingredients', )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass
