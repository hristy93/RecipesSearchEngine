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
from bs4 import BeautifulSoup

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
    for item in ingredients[:10]:
       print(item)
       stemmer(word)
       stemmer.print_word(word)

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


def main():

     # defines some variables and constants
    json_file_name = "recipes_500_refined_edited.json"
    user_likes_file_name = "recipes.csv"
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
    ingredients = get_ingredients(data)
    ingredients = list(ingredients)
    ingredients_count = len(ingredients)
    igredients_stop_words = ['сол', 'пипер', 'олио', 'лук', 'вода', 'черен_пипер']

     # prints general info about the recipe data
    print("\nRecipes data information:")
    print("recipes count: " + str(data_count))
    print("ingredients count: ", str(ingredients_count))

    #stemm_ingredients(ingredients)

    # processes the whole initial data from the json and gets the necessary data
    #process_data(data, ingredients, ingredient_data, ingredients_count_info)
    #print(ingredient_data[0])

    tfidf_raw_data = []
    meaningful_ingedients = []
    for recipe in data:
        #print(recipe['name'])
        ingredients_inner_data = []
        for item in recipe['ingredients']:
            ingredient_name = item['name']
            if ' ' in ingredient_name:
                ingredient_name = '_'.join(ingredient_name.split(' '))
            ingredients_inner_data.append(ingredient_name)
        meaningful_ingedients = [w for w in ingredients_inner_data if not w in igredients_stop_words]   
        ingredients_inner_data = " ".join(ingredients_inner_data)
        tfidf_raw_data.append(ingredients_inner_data)

    vectorizer = TfidfVectorizer(max_features = 10000, \
                                 #ngram_range = ( 1, 3 ), \
                                 sublinear_tf = True,
                                 binary = True,
                                 use_idf = True,
                                 stop_words = igredients_stop_words)

    result = vectorizer.fit_transform(tfidf_raw_data)
    #print('vocabulary', vectorizer.vocabulary_)
    idf_data = vectorizer.idf_
    print('Idf data')
    print(dict(zip(vectorizer.get_feature_names(), idf_data)))
    print('\n')
    feature_names = vectorizer.get_feature_names()
    print('Features count', str(feature_names.count))
    #print('feature_names', feature_names)
    tfidf_data = []

    #doc_index = 2
    #feature_index = result[doc_index,:].nonzero()[1]

    print('Tf data')
    for doc_index in range(1, data_count) :
        feature_index = result[doc_index,:].nonzero()[1]
        tfidf_score = zip(feature_index, [result[doc_index, x] for x in feature_index])
        tfidf_data.append(tfidf_score)
    for w, s in [(feature_names[i], s) for (i, s) in tfidf_score]:
        print(w, s)

    corpus_index = [n for n in range(1, data_count + 1)]
    import pandas as pd
    df = pd.DataFrame(result.todense(), index=feature_names, columns=corpus_index)
    print(df)

    #tfidf_data = get_tfidf_data(tf_data, idf_data, data_count)
    #print('Tf-idf data', tfidf_data)


    # From the exercise

    # First, we need some preparation.

    # Download text data sets, including stop word

    # nltk.download("stopwords")  


    #from nltk.corpus import stopwords # Import the stop word list
    #print(stopwords.words("english"))
    
    # 1. Remove HTML tags using the BeautifulSoup4 package
    #example1 = BeautifulSoup(example1, "html5lib").get_text() 
    
    # 2. Remove non-letters using regular expression which keeps only the letters from the Enlighs alphabet        
    #example1 = re.sub("[^a-zA-Z]", " ", example1) 
    
    # 3. Convert to lower case
    #example1 = example1.lower()
    
    # Split the text into words in order to remove the stop-words
    #words = example1.split()  
    
    # In Python, searching a set is much faster than searching
    #   a list, so convert the stop words to a set
    #stops = set(stopwords.words("english"))                  
    
    # 4. Remove stop words
    #meaningful_words = [w for w in words if not w in stops]
    
    # 5. Join the words back into one string
    #example1 = " ".join( meaningful_words )
    
    #Initialize the "CountVectorizer" object, which is scikit-learn's bag of words tool.  
    #vectorizer = CountVectorizer(analyzer = "word",   \
    #                             tokenizer = None,    \
    #                             preprocessor = None, \
    #                             stop_words = None,   \
    #                             max_features = 1000) 
    
    # fit_transform() does two functions: First, it fits the model
    # and learns the vocabulary; second, it transforms our training data
    # into feature vectors. The input to fit_transform should be a list of 
    # strings.
    #train_X = vectorizer.fit_transform(clean_train_reviews
    
    #Try using TfidfVectorizer instead of CountVectorizer and check how the results change.
    
    #vectorizer = TfidfVectorizer(max_features = 10000,   \
    #                             ngram_range = ( 1, 3 ), \
    #                             sublinear_tf = True )
    
    # Numpy arrays are easy to work with, so convert the result to an array
    # train_data_features = train_data_features.toarray()
    
    # Create features vectors for the validation set.
    
    #validation_X = vectorizer.transform(clean_validation_reviews)
    
    # Create features vectors for the validation set.
    
    #validation_X = vectorizer.transform(clean_validation_reviews)
    
    #predicted = model.predict( validation_X )
    
    #accuracy_score(validation["sentiment"], predicted)
    

if __name__ == "__main__":
        # enables the unicode console encoding on Windows
    if sys.platform == "win32":
        enable_win_unicode_console()
    main()

