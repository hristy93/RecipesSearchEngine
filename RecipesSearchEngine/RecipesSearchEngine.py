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
#from scipy.spatial.distance import cdist
#from scipy.spatial.distance import pdist
#import matplotlib.pyplot as plt
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


""" Reads the json data and saves it in data """
def read_json(json_file_name):
    data = []
    #print("Reading recipe data ...\n")
    with open(json_file_name, 'r', encoding="utf-8") as json_data:
        data = json.load(json_data)
    return data

""" Gets the ingreients from the json data """
def get_ingredients(data):
    ingredients = set()
    for item in data:
        for ingredient in item['ingredients']:
            if ingredient['name'] != '':
                ingredients.add(ingredient['name']) 
    #print("ingredients count: ", str(len(ingredients)))
    return ingredients

""" Stems the ingredients """
def stemm_ingredients(ingredients):
    stemmer = BulgarianStemmer('stem_rules_context_1.pkl') # or .txt
    stemmed_ingredients = set()
    for ingredient in ingredients:
        modified_ingredient = ""
        splitted_ingredient = ingredient.split(' ')
        if len(splitted_ingredient) > 1: 
            for splitted_item in splitted_ingredient:
                modified_ingredient = modified_ingredient + " " + stem(splitted_item)
                #print(splitted_item, " ", stemmer(splitted_item))
            print(ingredient, " ", modified_ingredient)
        else:
            modified_ingredient = stem(ingredient)
            print(ingredient, " ", modified_ingredient)
        stemmed_ingredients.add(modified_ingredient)

    return stemmed_ingredients
        #stemmer.print_word(item)

def process_data(data, ingredients, ingredient_data, ingredients_count_info):
    index = 0
    for recipe in data:
        #print(recipe['name'])
        ingredient_inner_data = []
        for ingredient in ingredients:
            is_found = False
            for item in recipe['ingredients']:
                if ingredient == item['name']:
                    is_found = True
                    break
            if is_found:
                ingredient_inner_data.append(1)
                if ingredients.index(ingredient) in ingredients_count_info.keys():
                    ingredients_count_info[ingredients.index(ingredient)] += 1
                else:
                    ingredients_count_info[ingredients.index(ingredient)] = 0
            else:
                ingredient_inner_data.append(0)
            #print(ingredients.index(ingredient))
        #print(str(len(ingredient_inner_data)))
        ingredient_data[index] = ingredient_inner_data
        index += 1
        #print(data.index(recipe))
        #ingredient_id[data.index(recipe)] = ingredient_data

    print("ingredient_data count: " + str(len(ingredient_data.values())))


""" Gets the tf-idf data from the tf_data and idf_data """
def get_tfidf_data(tf_data, idf_data, data_count):
    tfidf_data = list()
    for i in range(data_count):
        tf_list = tf_data[i]
        tfidf_data.append(np.dot(tf_list, idf_data))
    #print(tfidf_data)
    return tfidf_data


# Uses Solr to search with a single term for a recipe name
# that is close to the input 
def solr_single_term_recipe_name_search_by_field(solr_url, collection_name, search_input,
                                                search_field="name"):
    solr = SolrClient(solr_url)
    query = search_field + ":*" + search_input + "*"
    print("Single term recipe name search:")
    result = solr.query(collection_name,{
            'q':query,
    })
    result_data = result.data

    print("Results:")
    for docs in result.docs:
        print(docs['name'])


# Uses Solr to search with a phrase for a recipe name 
# that is exactly the same as the input 
def solr_phrase_search_recipe_name_by_field(solr_url, collection_name, search_input,
                                           search_field="name"):
    solr = SolrClient(solr_url)
    query = search_field + ":\"" + search_input + "\""
    print("\nPhrase recipe name search:")
    result = solr.query(collection_name,{
            'q':query,
    })
    result_data = result.data

    print("Results:")
    for docs in result.docs:
        print(docs['name'])


# Uses Solr to search with a single term for a recipe's ingredient
# that is close to the input 
def solr_single_term_search_ingredient_name_by_field(solr_url, collection_name,
                                                    search_input, search_field = "ingredients.name"):
    solr = SolrClient(solr_url)
    query = search_field + ":*" + search_input + "*"
    print("\nSingle term recipe ingredient search:")
    result = solr.query(collection_name,{
            'q':query,
    })
    result_data = result.data

    print("Results:")
    for docs in result.docs:
        print(docs['name'])


def solr_facet_search_recipe_category_by_field(solr_url, collection_name, search_input,
                                          search_field="name", facet_field="category"):
    solr = SolrClient(solr_url)
    query = search_field + ":*" + search_input + "*"
    print("\nCategory facet search:")
    result = solr.query(collection_name,{
            'q':query,
            'facet':'true',
            'facet.field':facet_field,
            'mincount':'1'
    })
    facets = result.get_facets()
    print("facets", facets, "\n")
    facet_values_as_list = result.get_facet_values_as_list(facet_field)
    print("facet_values_as_list", facet_values_as_list, "\n")
    facet_keys_as_list = result.get_facet_keys_as_list(facet_field)
    print("facet_keys_as_list", facet_keys_as_list, "\n")
    #jsonfacet_counts_as_dict = result.get_jsonfacet_counts_as_dict(facet_field, result.data)
    #print("jsonfacet_counts_as_dict", jsonfacet_counts_as_dict, "\n")
    result_data = result.data
    #print("result_data", result_data)
    #for docs in result.docs:
    #    print(docs['name'])


def solr_facet_search_recipe_user_by_field(solr_url, collection_name, search_input,
                                              search_field="name", facet_field="user_str"):
    solr = SolrClient(solr_url)
    query = search_field + ":*" + search_input + "*"
    print("\nUser facet search:")
    result = solr.query(collection_name,{
            'q':query,
            'facet':'true',
            'facet.field':facet_field,
    })
    facets = result.get_facets()
    print("facets", facets, "\n")
    facet_values_as_list = result.get_facet_values_as_list(facet_field)
    print("facet_values_as_list", facet_values_as_list, "\n")
    facet_keys_as_list = result.get_facet_keys_as_list(facet_field)
    print("facet_keys_as_list", facet_keys_as_list, "\n")
    result_data = result.data
    #print("result_data", result_data)
    #for docs in result.docs:
    #    print(docs['name'])


# NOT WORKING - need to remove the '>' and '<' from the durations and to make the corresponding 
# field into a an interger one (it's text now)
def solr_facet_search_recipe_duration_by_field(solr_url, collection_name, search_input,
                                              search_field="name", facet_field="duration", 
                                              duration_range = (10,50)):
    solr = SolrClient(solr_url)
    query = search_field + ":*" + search_input + "*"
    print("\nDuration facet search:")
    #duration_query = facet_field + ':[' + str(duration_range[0]) + '%28TO%28' + str(duration_range[1]) + ']'
    result = solr.query(collection_name,{
            'q':query,
            'facet':'true',
            'facet.range':facet_field,
            'facet.range.start':duration_range[0],
            'facet.range.end':duration_range[1],
            'facet.range.gap':0
    })
    facets = result.get_facets()
    print("facets", facets, "\n")
    facet_values_as_list = result.get_facet_values_as_list(facet_field)
    print("facet_values_as_list", facet_values_as_list, "\n")
    facet_keys_as_list = result.get_facet_keys_as_list(facet_field)
    print("facet_keys_as_list", facet_keys_as_list, "\n")
    result_data = result.data
    #print("result_data", result_data)
    #for docs in result.docs:
    #    print(docs['name'])


def main():

     # defines some variables and constants
    #json_file_name = "recipes_500_refined_edited.json"
    json_file_name = "recipes.json"
    user_likes_file_name = "recipes.csv"
    solr_url = "http://localhost:8983/solr"
    collection_name = "recipes-search-engine"

    propability_of_one = 0.6
    #users_count = 20
    best_user_pref_count = 5
    best_recipe_count = 5
    use_random_likes = False
    use_user_likes = False
    use_user_input = True
    tfidf_data = []

    # reads the recipes data from the json file
    data = read_json(json_file_name)

    # for recipe filtering by category id
    # recipe_category_id = 1
    # pe_category = ""
    # filter_data_by_category(recipe_category_id, data)

    # defines more variables
    data_count = len(data)
    ingredient_data = dict()
    ingredients_count_info = dict()
    ingredients = set()
    stemmed_ingredients = set()
    ingredients = get_ingredients(data)
    ingredients = list(ingredients)
    ingredients_count = len(ingredients)
    igredients_stop_words = ['сол', 'пипер', 'олио', 'лук', 'вода', 'черен_пипер']

    # prints general info about the recipe data
    print("\nRecipes data information:")
    print("recipes count: " + str(data_count))
    print("ingredients count: ", str(ingredients_count))

    # stemmes the ingredients
    #stemmed_ingredients = stemm_ingredients(ingredients)
    #print("stemmed_ingredients count", len(stemmed_ingredients))

    # processes the whole initial data from the json and gets the necessary data
    #process_data(data, ingredients, ingredient_data, ingredients_count_info)
    #print(ingredient_data[0])

    # Uses Solr to search into its index
    search_option = input("Search by partial recipe name (1), exact recipe name (2) or ingredient name (3)\n")
    search_input = input("\nSearch input: \n")


    # Facets from Solr
    #solr_facet_search_recipe_category_by_field(solr_url, collection_name, search_input)
    #solr_facet_search_recipe_user_by_field(solr_url, collection_name, search_input)
    #solr_facet_search_recipe_duration_by_field(solr_url, collection_name, search_input) # NOT WORKING
    if search_option == "1":
        solr_single_term_recipe_name_search_by_field(solr_url, collection_name, search_input)
    elif search_option == "2":
        solr_phrase_recipe_name_search_by_field(solr_url, collection_name, search_input)
    elif search_option == "3":
        solr_single_term_search_ingredient_name_by_field(solr_url, collection_name, search_input)
    solr_facet_search_recipe_category_by_field(solr_url, collection_name, search_input)
    solr_facet_search_recipe_user_by_field(solr_url, collection_name, search_input)
   #if " " not in search_input:
   #    solr_single_term_recipe_name_search_by_field(solr_url, collection_name, search_input)
   #else:
   #    solr_phrase_recipe_name_search_by_field(solr_url, collection_name, search_input)

    # Concatinates the separate names of the ingredients into someting like стар_праз_лук
    #tfidf_raw_data = []
    #meaningful_ingedients = []
    #for recipe in data:
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
    #vectorizer = TfidfVectorizer(max_features = 10000, \
    #                             #ngram_range = ( 1, 3 ), \
    #                             sublinear_tf = True,
    #                             binary = True,
    #                             use_idf = True,
    #                             stop_words = igredients_stop_words)
    #result = vectorizer.fit_transform(tfidf_raw_data)

    #print('vocabulary', vectorizer.vocabulary_)

    # Gets the idf data from the vectorizer's result
    #idf_data = vectorizer.idf_
    #print('Idf data')
    #print(dict(zip(vectorizer.get_feature_names(), idf_data)))
    #print('\n')

    # Gets the features' names from the vectorizer's result
    #feature_names = vectorizer.get_feature_names()
    #print('feature_names', feature_names)

    # Gets the tf-idf data from the vectorizer's result
    #print('Tf-idf data')
    #for doc_index in range(1, data_count) :
    #    feature_index = result[doc_index,:].nonzero()[1]
    #    tfidf_score = zip(feature_index, [result[doc_index, x] for x in feature_index])
    #    tfidf_data.append(tfidf_score)
    #for w, s in [(feature_names[i], s) for (i, s) in tfidf_score]:
    #    print(w, s)

    # Prints the tf-idf data of all recipes x ingredients
    #corpus_index = [n for n in range(1, data_count + 1)]
    #df = pd.DataFrame(result.todense(), index=corpus_index, columns=feature_names)
    #print(df)

    # Get the tf-idf data manually
    #tfidf_data = get_tfidf_data(tf_data, idf_data, data_count)
    #print('Tf-idf data', tfidf_data)
    

if __name__ == "__main__":
        # enables the unicode console encoding on Windows
    if sys.platform == "win32":
        enable_win_unicode_console()
    main()