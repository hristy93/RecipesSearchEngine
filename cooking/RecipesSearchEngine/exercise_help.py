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
