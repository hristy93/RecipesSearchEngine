# -*- coding: utf-8 -*-
import json
import sys
import math
import difflib
import time
import nltk
import re
from heapq import nlargest
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from itertools import compress
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.naive_bayes import GaussianNB
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
# from scipy.spatial.distance import cdist
# from scipy.spatial.distance import pdist
# import matplotlib.pyplot as plt

from bs4 import BeautifulSoup
from SolrClient import SolrClient
from transliterate import translit, get_available_language_codes


def enable_win_unicode_console():
    try:
        # Fix UTF8 output issues on Windows console.
        # Does nothing if package is not installed
        from win_unicode_console import enable
        enable()
    except ImportError:
        pass


def read_json(json_file_name):
    """ Reads the json data and saves it in data """
    data = []
    print("Reading the recipe data from the JSON file ...")
    with open(json_file_name, 'r', encoding="utf-8") as json_data:
        data = json.load(json_data)

    print("  Found {} recipes \n".format(len(data)))
    return data


def preprocess_ingredients(data, igredients_stop_words, write_back_ingredients):
    """ Prepocesses the ingredients from the json data """
    print("Preprocessing the recipes' ingredients ...")

    ingredients = set()
    stemmed_ingredients = set()
    common_ingredients_count = 0
    ingredients_count = 0

    for item in data:
        for ingredient in item['ingredients']:
            if ingredient['name'] != '':
                ingredients.add(ingredient['name'])
                ingredients_count += 1
                
                # Marks the ingredients from the stop words list as common
                if ingredient['name'] in igredients_stop_words or \
                    any([item for item in igredients_stop_words if item in ingredient['name']]):
                   
                    #print("  Marked {0} as common ingredient"
                    #      .format(ingredient['name']))
                    common_ingredients_count += 1
                    #del ingredient['name']
                    #data[recipe_index]['ingredients'][ingredient_index][
                    #    'common'] = '1'
                    ingredient['common'] = 1
                    
                # Gets the stemmed ingredients
                stemmed_ingredient = stemm_ingredient(ingredient['name'])
                stemmed_ingredients.add(stemmed_ingredient)

                # Writes back the stemmed ingredient into the data
                if write_back_ingredients:
                    data[recipe_index]['ingredients'][ingredient_index][
                        'name'] = stemmed_ingredient
    # print("ingredients count: ", str(len(ingredients)))

    print("  Found {0} common ingredients from {1}".format(common_ingredients_count, ingredients_count))
    print("  Found {0} unique ingredients from {1}".format(len(ingredients), ingredients_count))
    print("  Stemmed {0} ingedients from {1} unique ones".format(len(stemmed_ingredients), len(ingredients)))
    return ingredients, stemmed_ingredients, common_ingredients_count


def stemm_ingredient(ingredient):
    """ Stems the ingredient """
    # stemmer = BulgarianStemmer('stem_rules_context_1.pkl')  # or .txt
    stemmed_ingredient = ""
    splitted_ingredient = ingredient.split(' ')
    if len(splitted_ingredient) > 1:
        for splitted_item in splitted_ingredient:
            stemmed_ingredient = stemmed_ingredient + " " + stem(splitted_item)
            # print(splitted_item, " ", stemmer(splitted_item))
            # print(ingredient, " ", stemmed_ingredient)
    else:
        stemmed_ingredient = stem(ingredient)
        # print(ingredient, " ", stemmed_ingredient)

    return stemmed_ingredient
    # stemmer.print_word(item)


def stemm_ingredients(ingredients):
    """ Stems the ingredients """
    # stemmer = BulgarianStemmer('stem_rules_context_1.pkl')  # or .txt
    stemmed_ingredients = set()

    for ingredient in ingredients:
        modified_ingredient = ""
        splitted_ingredient = ingredient.split(' ')
        if len(splitted_ingredient) > 1:
            for splitted_item in splitted_ingredient:
                modified_ingredient = modified_ingredient + " " + stem(
                    splitted_item)
                # print(splitted_item, " ", stemmer(splitted_item))
            print(ingredient, " ", modified_ingredient)
        else:
            modified_ingredient = stem(ingredient)
            print(ingredient, " ", modified_ingredient)
        stemmed_ingredients.add(modified_ingredient)

    return stemmed_ingredients
    # stemmer.print_word(item)


def get_stemmed_categories(data, write_back_categories):
    """Stemms category for each recipe."""
    print("\nPreprocessing the recipes' categories ...")

    categories = set()
    stemmed_categories = set()
    unfiltered_recipes = {}

    similar_categories = {
        "супи": "суп",
        "супа": "суп"
    }
    for category, stemmed_category in similar_categories.items():
        categories.add(category)
        stemmed_categories.add(stemmed_category)

    for index, recipe in enumerate(data):
        # Replaces an unkonwn recipe category with "други"
        if recipe["category"] is None:
            recipe["category"] = "други"

        # Replaces a complex recipe category with a simpler one
        splitted_category = re.split('[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]', recipe["category"])
        if len(splitted_category) != 1:
            unfiltered_recipes[" ".join(splitted_category)] = index
            continue

        categories, stemmed_categories = preprocess_recipe_categories(
            recipe, categories, stemmed_categories, similar_categories,
            write_back_categories)

    for complex_category, recipe_index in unfiltered_recipes.items():
        simple_categories = complex_category.split()
        common = set(simple_categories).intersection(set(categories))
        if len(common) == 0:
            data[recipe_index]["category"] = simple_categories[0]
        else:
            data[recipe_index]["category"] = next(iter(common))

        categories, stemmed_categories = preprocess_recipe_categories(
            data[recipe_index], categories, stemmed_categories,
            similar_categories, write_back_categories)

    print("  Stemmed {0} categories from {1}".format(len(stemmed_categories), len(categories)))
    print("    Stemmed categories", stemmed_categories)
    return categories, stemmed_categories


def preprocess_recipe_categories(recipe, categories, stemmed_categories, similar_categories, write_back_categories):
    categories.add(recipe["category"])

    # Stemms the category
    stemm_category = stem(recipe["category"])
    # print(recipe["category"], "->", stemm_category)

    if write_back_categories:
        recipe["category"] = stemm_category

    if recipe["category"] not in similar_categories.keys():
        stemmed_categories.add(stemm_category)
    return categories, stemmed_categories


def process_data(data, ingredients, ingredient_data, ingredients_count_info):
    index = 0
    for recipe in data:
        # print(recipe['name'])
        ingredient_inner_data = []
        for ingredient in ingredients:
            is_found = False
            for item in recipe['ingredients']:
                if ingredient == item['name']:
                    is_found = True
                    break
            if is_found:
                ingredient_inner_data.append(1)
                if ingredients.index(
                        ingredient) in ingredients_count_info.keys():
                    ingredients_count_info[ingredients.index(ingredient)] += 1
                else:
                    ingredients_count_info[ingredients.index(ingredient)] = 0
            else:
                ingredient_inner_data.append(0)
                # print(ingredients.index(ingredient))
        # print(str(len(ingredient_inner_data)))
        ingredient_data[index] = ingredient_inner_data
        index += 1
        # print(data.index(recipe))
        # ingredient_id[data.index(recipe)] = ingredient_data

    print("ingredient_data count: " + str(len(ingredient_data.values())))


def get_tfidf_data(tf_data, idf_data, data_count):
    """ Gets the tf-idf data from the tf_data and idf_data """
    tfidf_data = list()
    for i in range(data_count):
        tf_list = tf_data[i]
        tfidf_data.append(np.dot(tf_list, idf_data))

    # print(tfidf_data)
    return tfidf_data


def solr_single_term_search_by_field(solr_url, collection_name,
                                     search_input, search_field="name"):
    """Uses Solr to search with a single term for a recipe name
    or ingredient name (depending on the value of search_field) 
    that is close to the input
    """
    solr = SolrClient(solr_url)
    query = "{0}:*{1}*".format(search_field, search_input)
    #print("Single term recipe name search:")
    result = solr.query(collection_name, {
        'q': query,
    })

    #result_data = result.data

    #print("Results:")
    #for docs in result.docs:
    #    print(docs['name'])

    return [doc["name"] for doc in result.docs]


def solr_phrase_search_by_field(solr_url, collection_name,
                                search_input, search_field="name"):
    """Uses Solr to search with a phrase for for a recipe name
    or ingredient name (depending on the value of search_field) 
    that is exactly the same as the input"""
    solr = SolrClient(solr_url)
    query = "{0}:\"{1}\"".format(search_field, search_input)
    #print("\nPhrase recipe name search:")
    result = solr.query(collection_name, {
        'q': query,
    })

    #result_data = result.data

    #print("Results:")
    #for docs in result.docs:
    #    print(docs['name'])

    return result.docs


def solr_facet_search_recipe_category_by_field(solr_url, collection_name,
                                               search_input,
                                               categories_facet_input_query,
                                               search_field="name",
                                               facet_field="category_str"):
    """Uses Solr to search with a facet for a recipe's category"""
    solr = SolrClient(solr_url)
    query = "{0}:*{1}*".format(search_field, search_input)
    print("\nCategory facet search:")
    result = solr.query(collection_name, {
        'q': query,
        'fq': categories_facet_input_query,
        'facet': 'true',
        'facet.field': facet_field,
        'mincount': '1'
    })
    facets = result.get_facets()
    print("  facets", facets, "\n")
    facet_values_as_list = result.get_facet_values_as_list(facet_field)
    print("  facet_values_as_list", facet_values_as_list, "\n")
    facet_keys_as_list = result.get_facet_keys_as_list(facet_field)
    print("  facet_keys_as_list", facet_keys_as_list, "\n")
    # jsonfacet_counts_as_dict = result.get_jsonfacet_counts_as_dict(facet_field, result.data)
    # print("jsonfacet_counts_as_dict", jsonfacet_counts_as_dict, "\n")
    result_data = result.data
    # print("result_data", result_data)
    # for docs in result.docs:
    #    print(docs['name'])
    return facets


def solr_facet_search_recipe_user_by_field(solr_url, collection_name,
                                           search_input,
                                           users_facet_input_query,
                                           search_field="name",
                                           facet_field="user_str"):
    """Uses Solr to search with a facet for a recipe's user"""
    solr = SolrClient(solr_url)
    query = "{0}:*{1}*".format(search_field, search_input)
    print("\nUser facet search:")
    result = solr.query(collection_name, {
        'q': query,
        'fq': users_facet_input_query,
        'facet': 'true',
        'facet.field': facet_field,
        'mincount': '1'
    })
    facets = result.get_facets()
    print("  facets", facets, "\n")
    facet_values_as_list = result.get_facet_values_as_list(facet_field)
    print("  facet_values_as_list", facet_values_as_list, "\n")
    facet_keys_as_list = result.get_facet_keys_as_list(facet_field)
    print("  facet_keys_as_list", facet_keys_as_list, "\n")
    result_data = result.data
    # print("result_data", result_data)
    # for docs in result.docs:
    #    print(docs['name'])
    return facets


def solr_facet_search_recipe_duration_by_field(solr_url, collection_name,
                                               search_input,
                                               duration_facet_input_query,
                                               duration_range=(0, 100),
                                               search_field="name",
                                               facet_field="duration"):
    """Uses Solr to search with a facet for a recipe's duration"""
    solr = SolrClient(solr_url)
    query = "{0}:*{1}*".format(search_field, search_input)
    print("\nDuration facet search:")
    # duration_query = facet_field + ':[' + str(duration_range[0]) + '%28TO%28' + str(duration_range[1]) + ']'
    result = solr.query(collection_name, {
        'q': query,
        'fq': duration_facet_input_query,
        'facet': 'true',
        'facet.range': facet_field,
        'facet.range.start': duration_range[0],
        'facet.range.end': duration_range[1],
        'facet.range.gap': 10
    })
    facets = result.get_facets()
    #request_url = result.url
    facet_ranges = result.get_facets_ranges()['duration']
    print("  facet_ranges", facet_ranges, "\n")
    result_data = result.data
    # print("result_data", result_data)
    # for docs in result.docs:
    #    print(docs['name'])
    return facet_ranges


def preprocess_data(data, igredients_stop_words, write_back_ingredients,
                    write_back_categories):
    """ Preprocesses the data from the JSON file """
    # Preprocesses the ingredients
    ingredients, stemmed_ingredients, common_ingredients_count =\
       preprocess_ingredients(data, igredients_stop_words, write_back_ingredients)

    # Preprocesses the categories
    categories, stemmed_categories = get_stemmed_categories(data, write_back_categories)
        
    return (ingredients, stemmed_ingredients, categories,
            stemmed_categories, common_ingredients_count)


def save_preprocessed_data_to_json(json_file_name, preprocessed_data):
    """ Prepocesses the data from the json """
    json_file_name_lenght = len(json_file_name) - json_file_name.rfind('/') - 1
    new_json_file_name = json_file_name[-json_file_name_lenght:-5] + "_preprocessed.json"
    with open(new_json_file_name, 'w', encoding="utf-8") as json_data:
        json.dump(preprocessed_data, json_data, ensure_ascii=False)


def preprocess_search_input(search_input, search_field):
    """ Preprocesses the search input """
    
    # Preprocesses the search input if it contains
    # only latin letters
    #is_latin = re.match("[a-zA-Z]*", search_input)
    #if is_latin:
    #   test = get_available_language_codes()
    #   test1 = translit(search_input, 'bg')

    # Checks if the search input is incorrect
    is_search_input_incorrect = re.search(r'[^а-яА-Я ]+', search_input)
    if is_search_input_incorrect:
        return None


    # Preprocesses the serach input if the search is it is a boolean query
    # with AND - 'и' and/or OR - 'или'
    if ' и ' in search_input or ' или ' in search_input:
       search_input = search_input.lower()
       search_input_splitted = search_input.split(' ')
       search_input = " ".join(["*{}*".format(stem(item)) for item in search_input_splitted])
       search_input = re.sub(' \*или\* ', ' OR ', search_input)
       search_input = re.sub(' \*и\* ', ' AND ', search_input)
       #replacer = re.compile(r'(\w+)')
       #search_input = replacer.sub(r'*\1*', search_input)

    return search_input


def get_incorrect_input_suggestion(search_input):
    """ Gets an suggestion about an incorrectly written
    search input
    """
    print("\nGetting suggestions about the incorrect input: {0}".format(search_input))
    suggested_search_input = re.sub(r'[^а-яА-Я ]+', '', search_input)
    print("  Result:", "\n", suggested_search_input)
    return suggested_search_input


def complex_search(solr_url, collection_name, search_input, search_field,
                   facet_fields, facet_input, duration_range = ()):
    """Uses Solr to do a complex search with all types of seaches 
    and facets
    """
    print("Searching for {0}".format(search_input))
    solr = SolrClient(solr_url)

    # Gets the preprocessed search input
    preprocessed_search_input = preprocess_search_input(search_input, search_field)
    
    # Checks if the search input is incorrect and suggests an alternative
    if preprocessed_search_input == None:
        print("Incorrect input!")
        incorrect_input_suggestion = get_incorrect_input_suggestion(search_input)
        return {"suggestion" : incorrect_input_suggestion}
    else:
        search_input = preprocessed_search_input

    query = "{0}:*{1}*".format(search_field, search_input)
    query_body = dict()
    query_body['q'] = query

    # Sets the facets to true if there are 
    #if len(facet_fields) != 0:
    #    query_body['facet'] = 'true'

    # Gets the categories facets input
    categories_facet_input_query = ""
    if "category" in facet_input.keys() and facet_input["category"]:
        categories_facet_input_query = "{!tag=CATEGORY}"
        categories_facet_input_query += "category:"
        categories_input = facet_input["category"]
        for item in categories_input:
            categories_facet_input_query += "*{0}* ".format(item)

    # Gets the users facets input
    users_facet_input_query = ""
    if "user_str" in facet_input.keys() and facet_input["user_str"]:
        users_facet_input_query = "{!tag=USER}"
        users_facet_input_query += "user:"
        users_input = facet_input["user_str"]
        for item in users_input:
            users_facet_input_query += "*{0}* ".format(item)

    # Gets the duration facets input
    duration_facet_input_query = ""
    if "duration" in facet_input.keys() and facet_input["duration"]:
        duration_facet_input_query = "{!tag=DURATION}"
        duration_facet_input_query += "duration:"
        duration_input = facet_input["duration"]
        duration_facet_input_query += "[{0} TO {1}]".format(
            duration_input[0], duration_input[1])

    facets_input_query = [categories_facet_input_query, users_facet_input_query,
        duration_facet_input_query]
    query_body['fq'] = facets_input_query
            
    # Gets the facets data
    if "category" in facet_fields and facet_input["category"]:
        categories_facet_results = solr_facet_search_recipe_category_by_field(
                                   solr_url, collection_name, search_input,
                                   facets_input_query, search_field)

    if "user_str" in facet_fields and facet_input["user_str"]:
        users_facet_result = solr_facet_search_recipe_user_by_field(
                             solr_url, collection_name, search_input,
                             facets_input_query, search_field)

    if "duration" in facet_fields and facet_input["duration"]:
        duration_facet_result = solr_facet_search_recipe_duration_by_field(
                                solr_url, collection_name, search_input,
                                facets_input_query, duration_range,
                                search_field)

    result = solr.query(collection_name, query_body)

    # Multi-select faceting 
        #'q': query,
        #'facet': 'true',
        #'json.facet':"{
        #sizes:{type:terms, field:size},
        #colors:{type:terms, field:color, domain:{excludeTags:COLOR} },
        #brands:{type:terms, field:brand, domain:{excludeTags:BRAND} }"

    #result_data = result.data

    url = result.url
    print("url: ", url, "\n")

    results_count = len(result.docs)
    spellcheck_data = result.data["spellcheck"]

    suggested_search_query_words, suggested_search_queries = [], []
    if not spellcheck_data["correctlySpelled"]:
        suggested_search_query_words, suggested_search_queries =\
           get_spellchecker_suggestions(solr_url,
                                        collection_name,
                                        search_input,
                                        search_field,
                                        spellcheck_data)
        # return suggested_search_query_words, suggested_search_queries

        #if not suggested_search_query_words and not suggested_search_queries:
        #    spitted_search_input = search_input.split(" ")
        #    for item in spitted_search_input:
        #        suggested_search_item_words, suggested_search_item =\
        #            get_spellchecker_suggestions(solr_url,
        #                                         collection_name,
        #                                         item,
        #                                         search_field,
        #                                         spellcheck_data)
    else:
        print("Found {0} results:".format(results_count))
        for docs in result.docs:
            print("  {}".format(docs['name']))

    #if results_count != 0:
    #    print("Found {0} results:".format(results_count))
    #    for docs in result.docs:
    #        print("  {}".format(docs['name']))
    #else:
        #spellcheck_data = result.data["spellcheck"]
        #suggested_search_inputs = get_spellchecker_suggestions(solr_url,
        #                                                       collection_name,
        #                                                       search_input,
        #                                                       search_field,
        #                                                       spellcheck_data)

    return result.docs, suggested_search_query_words, suggested_search_queries


def delete_all_documents_in_solr(solr_url, collection_name):
    """ Deletes all the recipes in the Solr collection
    """
    solr = SolrClient(solr_url)
    query = "commit=true&stream.body=<delete><query>*:*</query></delete>"
    print("\nDeleting all the documents in the solr collection {0}!"
          .format(collection_name))
    result = solr.query_raw(collection_name, query, "update")
    commit_result = solr.commit(collection_name)
    print("Result {0}".format(result))


def add_documents_in_solr(solr_url, collection_name, json_file_name, data):
    """ Adds the recipes in the JSON file (data) into the Solr
    collection
    """

    delete_all_documents_in_solr(solr_url, collection_name)


    print("\nAdding the documents in the JSON file {0} into the Solr " +\
       "collection {1}".format(json_file_name, collection_name))
    solr = SolrClient(solr_url)
    new_docs = list()
    new_recipe = dict()
    data_size = len(data)
    separation_length = 100
    print("Data lenght: ", data_size)
    if len(data) <= separation_length:
        start = 0
        end = data_size
    else:
        start = 0
        end = start + separation_length
        if end > data_size:
            end = data_size 
    while end <= data_size:
        print("start: ", str(start), " end: ", str(end))
        new_docs = list()
        new_recipe = dict()
        for new_recipe in data[start : end]:
            # Replaces the character '%' with it's corresponding word 
            # or it is escaped
            for ingredient in new_recipe["ingredients"]:
                for key, value in ingredient.items():
                    if type(value) is str and "%" in value:
                        ingredient[key] = re.sub("%"," процента ", value)
            for comment in new_recipe["comments"]:
                if "http" in comment[0] and "%" in comment[0]:
                    comment[0] = re.sub("%", "%25", comment[0])
                elif "%" in comment[0]:
                    comment[0] = re.sub("%", " процента ", comment[0])
            if "%" in new_recipe["instructions"]:
                new_recipe["instructions"] = re.sub("%"," процента ", new_recipe["instructions"])
            # Flattens the ingredients into separate key-value pairs
            new_recipe["ingredients.name"] = list()
            new_recipe["ingredients.unit"] = list()
            new_recipe["ingredients.quantity"] = list()
            new_recipe["ingredients.unstructured_data"] = list()
            new_recipe["ingredients.common"] = list()
            for ingredient_inner_data in new_recipe["ingredients"]:
                if ingredient_inner_data["common"] == "0":
                    new_recipe["ingredients.name"].append(ingredient_inner_data["name"])
                    new_recipe["ingredients.unit"].append(ingredient_inner_data["unit"])
                    new_recipe["ingredients.quantity"].append(ingredient_inner_data["quantity"])
                    new_recipe["ingredients.unstructured_data"].append(ingredient_inner_data["unstructured_data"])
                    new_recipe["ingredients.common"].append(ingredient_inner_data["common"])
            # Removes the complex ingredients data
            del new_recipe["ingredients"]
            new_docs.append(new_recipe)

        # Prepares and executes the needed queries in order to send data to Solr
        query = "?wt=json&{add:" + str(str(new_docs).encode('utf-8')) + "}&commit=true"
        result = solr.index_json(collection_name, json.dumps(new_docs))
        commit_result = solr.commit(collection_name)
        result = solr.query_raw(collection_name, query, "update/json/docs")
        commit_result = solr.commit(collection_name)
        print(result)

        start += separation_length
        end += separation_length
        #if start >= len(data) and end >= len(data):
        #    start -= separation_length
        #    end = len(data)
        if start < data_size and end >= data_size:
            end = data_size

def get_spellchecker_suggestions(solr_url, collection_name, search_input,
                                 search_field, spellcheck_data):
    """ Gets suggestions for the misspelled words in the query input 
    """
    suggested_search_query_words_info = dict()
    #input_words = search_input.split(" ")
    print("\nGetting the suggestions about the misspelled words in the query " +\
          "input {0}...".format(search_input))
    suggestions = spellcheck_data["suggestions"]
    for index, suggestion in enumerate(suggestions):
        if not isinstance(suggestion, dict):
            suggested_search_query_words_info[suggestions[index]] =\
                suggestions[index+1]["suggestion"]

    suggested_search_query_words = dict()
    for key, values in suggested_search_query_words_info.items():
        print("  Found {0} results for {1}:".format(len(values), key))
        suggested_search_query_words[key] = [value["word"] for value in values]
        print("    {}".format(suggested_search_query_words[key]))

    print("Getting the suggestions about the misspelled query " +\
          "input {0} ...".format(search_input))
    suggested_search_queries_info = list()
    suggested_search_queries_info = spellcheck_data["collations"]
    suggested_search_queries = list()
    print("  Found {0} results:".format(int(len(suggested_search_queries_info) / 2)))
    for suggested_search_query_info in suggested_search_queries_info:
        if isinstance(suggested_search_query_info, dict):
            raw_query = suggested_search_query_info["collationQuery"]
            query = raw_query[len(search_field) + 2:-1].lstrip("(").rstrip(")")
            suggested_search_queries.append(query)
            print("    {}".format(query))


    return suggested_search_query_words, suggested_search_queries

# WORKS FOR THE RECIPES' NAMES ONLY
# NEEDS TO BE FIXED IN THE SETTINGS AND SCHEMA
def generate_search_suggestions(solr_url, collection_name, search_input,
                                search_field):
    """ Genererates suggestions while entering an input in the search
    """
    solr = SolrClient(solr_url)
    search_input += "*"
    suggesters_results = list()

    # Finds which suggester to use based on the search field:
    # recipes' names or ingredeints's names
    if search_field == "name":
        fuzzy_suggester_name = "recipeNameFuzzySuggester"
        infix_suggester_name = "recipeNameInfixSuggester"
    elif search_field == "ingredients.name":
        fuzzy_suggester_name = "ingredientNameFuzzySuggester"
        infix_suggester_name = "ingredientNameInfixSuggester"

    new_query = {
        'suggest.build': 'true',
        'suggest.q': search_input,
        'suggest.dictionary': fuzzy_suggester_name
    }

    print("\nGeneration fuzzy suggestion on the input {0} ..."
          .format(search_input[:-1]))
    result = solr.query(collection_name, new_query, "suggest")

    # Gets the fuzzy suggestor's results

    fuzzy_suggester = result.data["suggest"][fuzzy_suggester_name][search_input]
    search_input_lenght = len(search_input[:-1])
    #fuzzy_suggester_results = [re.sub("^" + search_input[:-1], '<b>' + search_input[:-1] + '</b>', item["term"]) for item in fuzzy_suggester["suggestions"]]
    fuzzy_suggester_results = ['<b>' + search_input[0].upper() + search_input[1:-1] +\
                               '</b>' + item["term"][search_input_lenght:] for item
                               in fuzzy_suggester["suggestions"] if search_input in item]
    fuzzy_suggester_results_count = len(fuzzy_suggester_results)
    suggesters_results.extend(fuzzy_suggester_results)

    print("  Fuzzy suggester found {0} results:".format(fuzzy_suggester_results_count))
    for item in fuzzy_suggester_results:
        print("    {}".format(item))

    new_query = {
        'suggest.build': 'true',
        'suggest.q': search_input,
        'suggest.dictionary': infix_suggester_name
    }

    print("\nGeneration infix suggestion on the input {0} ..."
          .format(search_input[:-1]))
    result = solr.query(collection_name, new_query, "suggest")

    # Gets the infix suggestor's results
    infix_suggester = result.data["suggest"][infix_suggester_name][search_input]
    infix_suggester_results_count = infix_suggester["numFound"]
    infix_suggester_results = [item["term"] for item in infix_suggester["suggestions"] if not item["term"].startswith('<b>')]
    infix_suggester_results_count = len(infix_suggester_results)
    suggesters_results.extend(infix_suggester_results)

    print("   Infix suggester found {0} results:".format(infix_suggester_results_count))
    for item in infix_suggester_results:
        print("    {}".format(item))

    print("  The suggester found {0} results:".format(len(suggesters_results)))
    for item in fuzzy_suggester_results:
        print("    {}".format(item))

    return suggesters_results, [item["term"] for item in fuzzy_suggester["suggestions"]]


def more_like_this_recipe(solr_url, collection_name, search_input,
                          category, results_count = 5, search_field = "name"):
    """Uses Solr to search a similar recicpes to a given one"""
    print("\nFinding the recipes that are close to {0} ...".format(search_input))
    solr = SolrClient(solr_url)
    query = "{0}:\"{1}\"".format(search_field, search_input)
    #query += "AND ingredients.common:0^{0}".format(uncommon_ingredients_boost)
    result = solr.query(collection_name, {
        'q': query,
        'fl': "* , score",
        'fq': "category_str:{0}".format(stem(category))
    }, "mlt")

    result_data = result.data
    # print("result_data", result_data)

    print("  Found top {0} results:".format(results_count))
    for docs in result.docs[:results_count]:
        print("    {0}".format(docs['name']))

    return result.docs[:results_count]


def solr_search_recipes_by_category(solr_url, collection_name, search_input,
                               field="category", search_field="name"):
    """Uses Solr to search recipes by a given category"""
    print("\nFinding the recipes for category", search_input)
    solr = SolrClient(solr_url)
    stem_value = stem(search_input)
    query = "{0}_str:*{1}*".format(field, stem_value)
    result = solr.query(collection_name, {
        'q': query,
        'fl': search_field
    })

    print("  Found top {0} results:".format(len(result.docs)))
    return [r["name"] for r in result.docs]


def main():
    # Defines some variables and constants
    # json_file_name = "recipes_500_refined_edited.json"
    json_file_name = "scrapy_crawler/scrapy_crawler/recipes_new.json"
    solr_url = "http://localhost:8983/solr"
    collection_name = "recipes_search_engine"
    tfidf_data = []

    # Reads the recipes data from the json file
    data = read_json(json_file_name)

    # More variables
    data_count = len(data)
    ingredient_data = dict()
    ingredients_count_info = dict()
    # ingredients = set()
    stemmed_ingredients = set()
    # ingredients = list(ingredients)
    igredients_stop_words = ['сол', 'пипер', 'олио', 'лук', 'вода',
                             'захар', 'магданоз', 'босилек', 'подправк',
                            'кориандър', 'джодж', 'чубри', 'кими', 'дафинов',
                            'розмарин', 'мащерка', 'копър', 'зехтин']

    # Preprocesses the data from the json file
    write_back_ingredients = False
    write_back_categories = True
    (ingredients, stemmed_ingredients, categories,
        stemmed_categories, common_ingredients_count) =\
       preprocess_data(data, igredients_stop_words, 
                       write_back_ingredients, 
                       write_back_categories)
    ingredients_count = len(ingredients)

    # Saves the preprocessed data into a new file
    #save_preprocessed_data_to_json(json_file_name, data)

    # for recipe filtering by category id
    # recipe_category_id = 1
    # pe_category = ""
    # filter_data_by_category(recipe_category_id, data)

    # Prints general info about the recipe data
    print("\nRecipes data information:")
    print("  recipes count:", data_count)
    print("  unique ingredients count:", ingredients_count)
    print("  stemmed ingredients count:", len(stemmed_ingredients))
    print("  common ingredients count:", common_ingredients_count)
    print("  categories count", len(categories))
    print("  stemmed categories count", len(stemmed_categories))

    # Deletes all the recipes from the Solr collection
    #delete_all_documents_in_solr(solr_url, collection_name)

    # Adds JSON file data into the Solr collection
    #add_documents_in_solr(solr_url, collection_name, json_file_name, data)

    # Stemmes the ingredients
    # stemmed_ingredients = stemm_ingredients(ingredients)
    # print("stemmed_ingredients count", len(stemmed_ingredients))

    # Processes the whole initial data from the json and gets the necessary data
    # process_data(data, ingredients, ingredient_data, ingredients_count_info)
    # print(ingredient_data[0])

    # Search recipes by category
    # res = solr_search_recipes_by_category(solr_url, collection_name, "салата")
    # print(res)

    # Complex query inputs for the complex search
    facet_input = dict()
    facet_fields = ["category", "user_str", "duration"]
    #facet_input["category"] = ["основ", "сал"]
    #duration_range = (20, 40)
    facet_input["duration"] = duration_range
    facet_input["user_str"] = ["Гомеш"]
    facet_input["category"] = ["дес", "осн"]
    search_input = "сла"
    search_field = "ingredients.name"

    # Multiple query inputs for the complex search
    duration_range = (0, 100)
    #search_input = "картофи или пиле"
    #search_input = "kartofi ili pile"
    #search_input = "картофи или пиле"
    #search_input = "Пай с пуйка и шунка"
    #search_field = "name"

    # Query inputs for the spellchecker
    #duration_range = (0, 300)
    #search_input = "школод"
    #search_input = "пилашко месо"
    #search_input = "шоколдови бисвити"
    #search_input = "шоколадови бисквити"
    #search_input = "червенаябълка"

    #search_field = "name"

    #search_input = "канелен"
    #search_field = "name"
    #duration_range = (0, 300)
 
    # Uses Solr to do a complex search into it's index
    complex_search(solr_url, collection_name, search_input, search_field,
                   facet_fields, facet_input, duration_range)

    # Generates suggestions to words while entering a search query
    #search_input = input("\nSearch input: \n")
    #search_input = "шок"
    #search_field = "ingredients.name"
    #search_field = "name"
    #generate_search_suggestions(solr_url, collection_name, search_input,
    #                            search_field)

    # Generates recipes similar to a given one
    #search_input = "Пилешки бутчета с уиски и картофено пюре"
    #category = "основно"
    #search_input = "ябълкови сандвичи"
    #category = "десерт"
    #results_count = 5
    #more_like_this_recipe(solr_url, collection_name, search_input,
    #                      category)

    """
    # Uses Solr to search into its index
    search_option = input(
        "\nSearch by recipe name (1) or ingredient name (2)\n")
    search_input = input("\nSearch input: \n")
    
    if search_option == "1":
        print("\nSingle term recipe name search:")
        docs_found = solr_single_term_search_by_field(solr_url, collection_name,
                                                     search_input,
                                                     search_field="name")
    elif search_option == "2":
         print("\nSingle term recipe ingredient search:")
         docs_found = solr_single_term_search_by_field(solr_url, collection_name,
                                                     search_input,
                                                     search_field="ingredients.name")

    print("Results: {0} found".format(len(docs_found)))
    for docs in docs_found:
        print(docs['name'])

    if len(docs_found) != 0:
        # Facets from Solr
        solr_facet_search_recipe_category_by_field(solr_url, collection_name,
                                                   search_input)
        solr_facet_search_recipe_user_by_field(solr_url, collection_name,
                                               search_input)
        solr_facet_search_recipe_duration_by_field(solr_url, collection_name,
                                               search_input)
    else:
        print("No docs found")
    """

    ## if " " not in search_input:
    ##    solr_single_term_recipe_name_search_by_field(solr_url, collection_name, search_input)
    ## else:
    ##    solr_phrase_recipe_name_search_by_field(solr_url, collection_name, search_input)

    # Concatinates the separate names of the ingredients into someting like стар_праз_лук
    # tfidf_raw_data = []
    # meaningful_ingedients = []
    # for recipe in data:
    #    #print(recipe['name'])
    #    ingredients_inner_data = []
    #    for item in recipe['ingredients']:
    #        ingredient_name = item['name']
    #        if ' ' in ingredient_name:
    #            ingredient_name = '_'.join(ingredient_name.split(' '))
    #        ingredients_inner_data.append(ingredient_name)
    #    meaningful_ingedients = [w for w in ingredients_inner_data if not w in igredients_stop_words]
    #    ingredients_inner_data = " ".join(ingredients_inner_data)
    #    tfidf_raw_data.append(ingredients_inner_data)

    # Uses a vectorizer to make get the tf-idf data
    # vectorizer = TfidfVectorizer(max_features = 10000, \
    #                             #ngram_range = ( 1, 3 ), \
    #                             sublinear_tf = True,
    #                             binary = True,
    #                             use_idf = True,
    #                             stop_words = igredients_stop_words)
    # result = vectorizer.fit_transform(tfidf_raw_data)

    # print('vocabulary', vectorizer.vocabulary_)

    # Gets the idf data from the vectorizer's result
    # idf_data = vectorizer.idf_
    # print('Idf data')
    # print(dict(zip(vectorizer.get_feature_names(), idf_data)))
    # print('\n')

    # Gets the features' names from the vectorizer's result
    # feature_names = vectorizer.get_feature_names()
    # print('feature_names', feature_names)

    # Gets the tf-idf data from the vectorizer's result
    # print('Tf-idf data')
    # for doc_index in range(1, data_count) :
    #    feature_index = result[doc_index,:].nonzero()[1]
    #    tfidf_score = zip(feature_index, [result[doc_index, x] for x in feature_index])
    #    tfidf_data.append(tfidf_score)
    # for w, s in [(feature_names[i], s) for (i, s) in tfidf_score]:
    #    print(w, s)

    # Prints the tf-idf data of all recipes x ingredients
    # corpus_index = [n for n in range(1, data_count + 1)]
    # df = pd.DataFrame(result.todense(), index=corpus_index, columns=feature_names)
    # print(df)

    # Get the tf-idf data manually
    # tfidf_data = get_tfidf_data(tf_data, idf_data, data_count)
    # print('Tf-idf data', tfidf_data)

SOLR_URL = "http://localhost:8983/solr"
JSON_FILENAME = "scrapy_crawler/scrapy_crawler/recipes.json"
# json_file_name = "recipes_500_refined_edited.json"


def call_recipes():
    def main():
        # Defines some variables and constants
        collection_name = "recipes_search_engine"
        tfidf_data = []

        # Reads the recipes data from the json file
        data = read_json(JSON_FILENAME)

        # More variables
        data_count = len(data)
        ingredient_data = dict()
        ingredients_count_info = dict()
        # ingredients = set()
        stemmed_ingredients = set()
        # ingredients = list(ingredients)
        igredients_stop_words = ['сол', 'пипер', 'олио', 'лук', 'вода',
                                 'захар', 'магданоз', 'босилек', 'подправк',
                                 'кориандър',
                                 'канела', 'джодж', 'чубри', 'кими', 'дафинов',
                                 'розмарин', 'мащерка', 'копър', 'зехтин']

        # Preprocesses the data from the json file
        write_back_ingredients = False
        write_back_categories = True
        (ingredients, stemmed_ingredients, categories,
         stemmed_categories, common_ingredients_count) = \
            preprocess_data(data, igredients_stop_words,
                            write_back_ingredients,
                            write_back_categories)
        ingredients_count = len(ingredients)

        # Saves the preprocessed data into a new file
        # save_preprocessed_data_to_json(json_file_name, data)

        # for recipe filtering by category id
        # recipe_category_id = 1
        # pe_category = ""
        # filter_data_by_category(recipe_category_id, data)

        # Prints general info about the recipe data
        print("\nRecipes data information:")
        print("  recipes count:", data_count)
        print("  unique ingredients count:", ingredients_count)
        print("  stemmed ingredients count:", len(stemmed_ingredients))
        print("  common ingredients count:", common_ingredients_count)
        print("  categories count", len(categories))
        print("  stemmed categories count", len(stemmed_categories))

        # Deletes all the recipes from the Solr collection
        # delete_all_documents_in_solr(solr_url, collection_name)

        # Adds JSON file data into the Solr collection
        # add_documents_in_solr(solr_url, collection_name, json_file_name, data)

        # Stemmes the ingredients
        # stemmed_ingredients = stemm_ingredients(ingredients)
        # print("stemmed_ingredients count", len(stemmed_ingredients))

        # Processes the whole initial data from the json and gets the necessary data
        # process_data(data, ingredients, ingredient_data, ingredients_count_info)
        # print(ingredient_data[0])

        # Complex query inputs for the complex search
        facet_input = dict()
        facet_fields = ["category", "user_str", "duration"]
        # facet_input["category"] = ["основ", "сал"]
        duration_range = (20, 40)
        facet_input["duration"] = duration_range
        facet_input["user_str"] = ["Гомеш"]
        facet_input["category"] = ["дес", "осн"]
        search_input = "сла"
        search_field = "ingredients.name"

        # Multiple query inputs for the complex search
        duration_range = (0, 100)
        # search_input = "картофи или пиле"
        # search_input = "kartofi ili pile"
        # search_input = "картофи или пиле"
        # search_input = "Пай с пуйка и шунка"
        # search_field = "name"

        # Query inputs for the spellchecker
        # duration_range = (0, 100)
        # search_input = "школод"
        # search_input = "пилашко месо"
        # search_input = "шоколдови бисвити"
        # search_field = "name"

        # Uses Solr to do a complex search into it's index
        complex_search(SOLR_URL, collection_name, search_input, search_field,
                       facet_fields, facet_input, duration_range)


if __name__ == "__main__":
    from bulgarian_stemmer.bulgarian_stemmer import BulgarianStemmer
    from bulgarian_stemmer.bulstem import *

    # enables the unicode console encoding on Windows
    if sys.platform == "win32":
        enable_win_unicode_console()
    main()
else:
    from .bulgarian_stemmer.bulgarian_stemmer import BulgarianStemmer
    from .bulgarian_stemmer.bulstem import *
