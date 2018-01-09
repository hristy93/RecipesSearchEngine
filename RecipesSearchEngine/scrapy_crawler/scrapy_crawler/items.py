# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.contrib.loader import ItemLoader
from scrapy.contrib.loader.processor import TakeFirst
import re

def serialize_recipe_instructions(value):
    if isinstance(value, int):
        return value
    else:
        return '\n'.join(value)

# NOT WORKING
def serialize_recipe_rating(value):
    if value == '0':
        return ''
    else:
        return value
  
def serialize_ingredient_name(value):
    return value.partition(' ')[2:]

def serialize_ingredient_quantity(value):
    return value.partition(' ')[0]

def serialize_ingredient_unit(value):
    return value.partition(' ')[1]

def serialize_recipe_comments(comments):
    processed_comments = list()
    for comment_data in comments:
        comment_data = [comment.lstrip().rstrip().strip("\n") for comment in comment_data if comment != "\n"]
        processed_comments.append(comment_data)
    return processed_comments

# NOT WORKING
def serialize_recipe_duration(value):
    return re.findall('\d+', value )[0]

    #partitioned_item = value.split(' ')
    #if  partitioned_item[0] in ['<', '>']:
    #    return partitioned_item[0] + ' ' + partitioned_item[1] 
    #else:
    #    return  partitioned_item[0] 

class IngredientItem(scrapy.Item):
    name = scrapy.Field(serializer=serialize_ingredient_name)
    quantity = scrapy.Field(serializer=serialize_ingredient_quantity)
    unit = scrapy.Field(serializer=serialize_ingredient_unit)
    unstructured_data = scrapy.Field()
    is_allergic = scrapy.Field()

class RecipeItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    instructions = scrapy.Field()
    duration = scrapy.Field(serializer=serialize_recipe_duration)
    duration_bound = scrapy.Field()
    ingredients = scrapy.Field()
    difficulty = scrapy.Field()
    servings = scrapy.Field()
    user = scrapy.Field()
    category = scrapy.Field()
    #dish = scrapy.Field()
    #region = scrapy.Field()
    image_url = scrapy.Field()
    comments = scrapy.Field(serializer=serialize_recipe_comments)
    #comments = scrapy.Field()
    rating = scrapy.Field()
    url = scrapy.Field()

#class Ingredients(scrapy.Item):
#    ingredients = scrapy.Field()

#class RecipeItemLoader(ItemLoader):
#    default_item_class = RecipeItem
#    default_output_processor = TakeFirst()

#class IngredientItemLoader(ItemLoader):
#    default_item_class = IngredientItem
#    default_output_processor = TakeFirst()
