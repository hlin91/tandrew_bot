#======================================================================
# Chatbot module for Tandrew-bot
#======================================================================
import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import numpy
import tensorflow
import tflearn
import random
import json
import pickle
import os

with open('intents.json') as file:
    data = json.load(file)
try: # Try to load the training data from a file
    with open('data.pickle', 'rb') as f:
        words, labels, training, output = pickle.load(f)
except:
    words = []
    labels = []
    docs_x = []
    docs_y = []
    # Load json file into lists
    for intent in data['intents']:
        for pattern in intent['patterns']:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent['tag'])
        if intent['tag'] not in labels:
            labels.append(intent['tag'])
    # Create a list of unique word stems
    words = [stemmer.stem(w.lower()) for w in words if w != '?']
    words = sorted(list(set(words)))
    labels = sorted(labels)
    # Generate a bag of words so that we can encode sentences as binary strings with length equal to the bag size
    training = []
    output = []
    out_empty = [0 for _ in range(len(labels))]
    for x, doc in enumerate(docs_x):
        bag = []
        wrds = [stemmer.stem(w.lower()) for w in doc]
        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)
        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1
        training.append(bag)
        output.append(output_row)
    training = numpy.array(training)
    output = numpy.array(output)
    # Serialize the training data
    with open('data.pickle', 'wb') as f:
        pickle.dump((words, labels, training, output), f)
# Create and train the model
tensorflow.reset_default_graph()
net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation = 'softmax')
net = tflearn.regression(net)
model = tflearn.DNN(net)
try: # Try to load the model from a file
    model.load('model.tflearn')
except:
    model.fit(training, output, n_epoch=1000, batch_size=8, show_metric=True)
    model.save('model.tflearn')

# Interact with the model
def bag_of_words(s, words): # Convert an input string into a binary string with words as bag
    bag = [0 for _ in range(len(words))]
    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]
    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1
    return numpy.array(bag)
def chat(inp):
    results = model.predict([bag_of_words(inp, words)])
    results_index = numpy.argmax(results)
    tag = labels[results_index]
    for tg in data['intents']:
        if tg['tag'] == tag:
            responses = tg['responses']
    return random.choice(responses)
