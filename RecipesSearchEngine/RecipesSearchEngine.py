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
from bulgarian_stemmer.bulgarian_stemmer import BulgarianStemmer
from bulgarian_stemmer.bulstem import *
from bs4 import BeautifulSoup
from SolrClient import SolrClient


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


def preprocess_ingredients(data, igredients_stop_words):
    """ Prepocesses the ingredients from the json data """
    print("Preprocessing the recipes' ingredients ...")

    ingredients = set()
    stemmed_ingredients = set()
    common_ingredients_count = 0

    for recipe_index, item in enumerate(data):
        for ingredient_index, ingredient in enumerate(item['ingredients']):
            if ingredient['name'] != '':
                
                # Marks the ingredients from the stop words list as common
                #test = any([re.match(".*{}.*".format(ingredient['name']), item) for 
                #        item in igredients_stop_words])
                #if ingredient['name'] == "кафява захар":
                #    pass
                #if test:
                    #print(ingredient['name'])
                if ingredient['name'] in igredients_stop_words or \
                    any([item for item in igredients_stop_words if item in ingredient['name']]):
                   
                    #print("  Marked {0} as common ingredient"
                    #      .format(ingredient['name']))
                    common_ingredients_count += 1
                    #del ingredient['name']
                    data[recipe_index]['ingredients'][ingredient_index][
                        'common'] = '1'
                else:
                    ingredients.add(ingredient['name'])

                    # Gets the stemmed ingredients
                    stemmed_ingredient = stemm_ingredient(ingredient['name'])

                    # Writes back the stemmed ingredient into the data
                    data[recipe_index]['ingredients'][ingredient_index][
                        'name'] = stemmed_ingredient
                    stemmed_ingredients.add(stemmed_ingredient)
    # print("ingredients count: ", str(len(ingredients)))

    print("  Found {0} common ingredients from {1}".format(common_ingredients_count, len(ingredients)))
    print("  Stemmed {0} ingedients from {1}".format(len(stemmed_ingredients), len(ingredients)))
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


def get_stemmed_categories(data):
    """Stemms category for each recipe."""
    print("\nPreprocessing the recipes' categories ...")

    categories = set()
    stemmed_categories = set()

    for recipe in data:
        categories.add(recipe["category"])
        if recipe["category"] is None:
            recipe["category"] = ""
        stemm_category = stem(recipe["category"])
        # print(recipe["category"], "->", stemm_category)
        recipe["category"] = stemm_category
        stemmed_categories.add(stemm_category)

    print("  Stemmed {0} categories from {1}".format(len(stemmed_categories), len(categories)))
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

    return result.docs


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
                                               facet_field="category"):
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


def preprocess_data(data, igredients_stop_words):
    """ Preprocesses the data from the json """
    # Preprocesses the ingredients
    ingredients, stemmed_ingredients, common_ingredients_count =\
       preprocess_ingredients(data, igredients_stop_words)

    # Preprocesses the categories
    categories, stemmed_categories = get_stemmed_categories(data)
        
    return (ingredients, stemmed_ingredients, categories,
            stemmed_categories, common_ingredients_count)


def save_preprocessed_data_to_json(json_file_name, preprocessed_data):
    """ Prepocesses the data from the json """
    new_json_file_name = json_file_name[-12:-5] + "_preprocessed.json"
    with open(new_json_file_name, 'w', encoding="utf-8") as json_data:
        json.dump(preprocessed_data, json_data, ensure_ascii=False)

def complex_search(solr_url, collection_name, search_input, search_field,
                   facet_fields, facet_input, duration_range):
    """Uses Solr to do a complex search with all types of seaches 
    and facets
    """
    solr = SolrClient(solr_url)
    query = "{0}:*{1}*".format(search_field, search_input)
    query_body = dict()
    query_body['q'] = query

    # Sets the facets to true if there are 
    #if len(facet_fields) != 0:
    #    query_body['facet'] = 'true'

    # Gets the categories facets input
    categories_facet_input_query = ""
    if "category" in facet_input.keys():
        categories_facet_input_query = "{!tag=CATEGORY}"
        categories_facet_input_query += "category:"
        categories_input = facet_input["category"]
        for item in categories_input:
            categories_facet_input_query += "*{0}* ".format(item)

    # Gets the users facets input
    users_facet_input_query = ""
    if "user_str" in facet_input.keys():
        users_facet_input_query = "{!tag=USER}"
        users_facet_input_query += "user:"
        users_input = facet_input["user_str"]
        for item in users_input:
            users_facet_input_query += "*{0}* ".format(item)

    # Gets the duration facets input
    duration_facet_input_query = ""
    if "duration" in facet_input.keys():
        duration_facet_input_query = "{!tag=DURATION}"
        duration_facet_input_query += "duration:"
        duration_input = facet_input["duration"]
        duration_facet_input_query += "[{0} TO {1}]".format(
            duration_input[0], duration_input[1])

    facets_input_query = [categories_facet_input_query, users_facet_input_query,
        duration_facet_input_query]
    query_body['fq'] = facets_input_query
            
    # Gets the facets data
    if "category" in facet_fields:
        categories_facet_results = solr_facet_search_recipe_category_by_field(
                                   solr_url, collection_name, search_input,
                                   facets_input_query, search_field)

    if "user_str" in facet_fields:
        users_facet_result = solr_facet_search_recipe_user_by_field(
                             solr_url, collection_name, search_input,
                             facets_input_query, search_field)

    if "duration" in facet_fields:
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
    print("url: ", url)

    results_count = len(result.docs)
    if results_count != 0:
        print("Found {0} results:".format(results_count))
        for docs in result.docs:
            print(print("  {}".format(docs['name'])))
    else:
        spellcheck_data = result.data["spellcheck"]
        suggested_search_inputs = get_spellchecker_suggestions(solr_url,
                                                               collection_name,
                                                               search_input,
                                                               spellcheck_data)

    return result.docs


def delete_all_documents_in_solr(solr_url, collection_name):
    """ Deletes all the recipes in the Solr collection
    """
    solr = SolrClient(solr_url)
    query = "commit=true&stream.body=<delete><query>*:*</query></delete>"
    print("\nDeleting all the documents in the solr collection {0}!"
          .format(collection_name))
    result = solr.query_raw(collection_name, query, "update")
    print("Result {0}".format(result))


# NOT WORKING
#def add_documents_in_solr(solr_url, collection_name, json_file_name, data):
#    """ Adds the recipes in the JSON file (data) into the Solr
#    collection
#    """
#    solr = SolrClient(solr_url)
#    query = "?wt=json&{add:" + str(str(data[0]).encode('utf-8')) + "}&commit=true"
#    print("\nAdding the documents in the JSON file {0} into the Solr " +\
#       "collection {1}".format(json_file_name, collection_name))
#    result = solr.query(collection_name,query, "update/json/docs")
#    #add_data = dict()
#    #for item in data:
#    #    add_data["add"] = dict()
#    #    add_data["add"]["doc"] = item
#    #print(data[0])
#    #result= solr.(collection_name,[add_data])
#    print(result)


def get_spellchecker_suggestions(solr_url, collection_name, search_input,
                                      spellcheck_data):
    """ Gets suggestions for the misspelled words in the query input 
    """
    suggested_search_inputs = dict()
    #input_words = search_input.split(" ")
    suggestions = spellcheck_data["suggestions"]
    for suggestion in suggestions[1:]:
        suggested_search_inputs[suggestions[0]] = suggestion["suggestion"]

    return suggested_search_inputs


def generate_search_suggestions(solr_url, collection_name, search_input):
    """ Genererates suggestions while entering an input in the search
    """
    solr = SolrClient(solr_url)
    search_input += "*"
    new_query = {
        'suggest.build': 'true',
        'suggest.q': search_input
    }
    print("\nGeneration suggestion on the input {0} ..."
          .format(search_input[:-1]))
    result = solr.query(collection_name, new_query, "suggest")

    suggesters = result.data["suggest"]
    suggesters_results = list()

    # Gets the fuzzy suggestor's results
    fuzzy_suggester = suggesters["fuzzySuggester"][search_input]
    fuzzy_suggester_results_count = fuzzy_suggester["numFound"]
    search_input_lenght = len(search_input[:-1])
    #fuzzy_suggester_results = [re.sub("^" + search_input[:-1], '<b>' + search_input[:-1] + '</b>', item["term"]) for item in fuzzy_suggester["suggestions"]]
    fuzzy_suggester_results = ['<b>' + search_input[0].upper() + search_input[1:-1] + '</b>' + item["term"][search_input_lenght:] for item in fuzzy_suggester["suggestions"]]
    suggesters_results.extend(fuzzy_suggester_results)

    print("  Fuzzy suggester found {0} results:".format(fuzzy_suggester_results_count))
    for item in fuzzy_suggester_results:
        print("    {}".format(item))

    # Gets the infix suggestor's results
    infix_suggester = suggesters["infixSuggester"][search_input]
    infix_suggester_results_count = infix_suggester["numFound"]
    infix_suggester_results = [item["term"] for item in infix_suggester["suggestions"] if not item["term"].startswith('<b>')]
    infix_suggester_results_count = len(infix_suggester_results)
    suggesters_results.extend(infix_suggester_results)

    print("   Infix suggester found {0} results:".format(infix_suggester_results_count))
    for item in infix_suggester_results:
        print("    {}".format(item))

    #print("  The suggester found {0} results:".format(len(suggesters_results)))
    #for item in fuzzy_suggester_results:
    #    print("    {}".format(item))

    return suggesters_results


def main():
    # Defines some variables and constants
    # json_file_name = "recipes_500_refined_edited.json"
    json_file_name = "scrapy_crawler/scrapy_crawler/recipes.json"
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
                             'захар', 'магданоз', 'босилек', 'подправк', 'кориандър',
                            'канела', 'джодж', 'чубри', 'кими', 'дафинов',
                            'розмарин', 'мащерка', 'копър']

    # Preprocesses the data from the json file
    (ingredients, stemmed_ingredients, categories,
        stemmed_categories, common_ingredients_count) =\
       preprocess_data(data, igredients_stop_words)
    ingredients_count = len(ingredients)

    # Saves the preprocessed data into a new file
    save_preprocessed_data_to_json(json_file_name, data)

    # for recipe filtering by category id
    # recipe_category_id = 1
    # pe_category = ""
    # filter_data_by_category(recipe_category_id, data)

    # Prints general info about the recipe data
    print("\nRecipes data information:")
    print("  recipes count:", data_count)
    print("  ingredients count:", ingredients_count)
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

    # Uses Solr to do a complex search into it's index
    facet_input = dict()
    facet_fields = ["category", "user_str", "duration"]

    ##facet_input["category"] = ["основ", "сал"]
    #duration_range = (20, 40)
    #facet_input["duration"] = duration_range
    #facet_input["user_str"] = ["Гомеш"]
    #facet_input["category"] = ["дес", "осн"]
    #search_input = "сла"
    #search_field = "ingredients.name"

    duration_range = (0, 100)
    search_input = "школод"
    #search_input = "шпилашко месо"
    search_field = "ingredients.name"
 
    # Uses Solr to do a complex search into it's index
    complex_search(solr_url, collection_name, search_input, search_field,
                   facet_fields, facet_input, duration_range)

    # Generates suggestions to words while entering a search query
    #search_input = input("\nSearch input: \n")
    #generate_search_suggestions(solr_url, collection_name, search_input)

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


if __name__ == "__main__":
    # enables the unicode console encoding on Windows
    if sys.platform == "win32":
        enable_win_unicode_console()
    main()
