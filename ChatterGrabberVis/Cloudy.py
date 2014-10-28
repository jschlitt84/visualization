import nltk
import sys
import unicodedata
import datetime

from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
from dateutil import parser
from copy import deepcopy
from wordcloud import WordCloud

import matplotlib.pyplot as plt

blockKeys = ['$!','$?','$...','#yesallwomen']
stopWords = stopwords.words('english')
lmtzr = WordNetLemmatizer()


def lemList(listed):
    listed = list(set([lmtzr.lemmatize(word) for word in listed if len(word)>1]))


def stripUnicode(text):
    """Strips unicode special characters for text storage (smileys, etc)"""
    if text == None:
        return "NaN"
    else:
        if type(text) == unicode:
            return str(unicodedata.normalize('NFKD', text).encode('ascii', 'ignore'))
        else:
            return str(text)


def prepTweet(word):
    word =  stripUnicode(word)
    original = text = str(word)
    
    text = text.replace("&amp",'') #cleanup conversion bug
    toAdd = set()
        
    if '?' in text:
	toAdd.add('$?')
    if '!' in text:
	toAdd.add('$!')
    if '...' in text:
	toAdd.add('$...')

    punctuations = ".,\"-_%!?=+\n\t:;()*&$/"
    
    #Remove accentuated characters
    text = unicode(text)
    text = ''.join(char for char in unicodedata.normalize('NFD', text) if unicodedata.category(char) != 'Mn')
        
    #End of string operations, continuing with list ops.    
    

    while 'http' in text:
	toAdd.add('$link')
	temp = text.index('http')
	text = text[:temp] + text[text.find(' ',temp):]
    while 'RT @' in text:
	toAdd.add('$RT')
	temp = text.index('RT @')
	text = text[:temp] + text[text.find(' ',temp):]
    """while '@' in text:
	toAdd.add('@user')
	temp = text.index('@')
	if temp == len(text) - 1:
		text = text[:-1]
	else:
		text = text[:temp] + text[text.find(' ',temp):]"""
    for char in punctuations:
	text = text.replace(char,' ')
    while '  ' in text:
        text = text.replace('  ',' ')
    while text.startswith(' '):
        text = text[1:]
    while text.endswith(' '):
        text = text[:-1]
    listed = text.lower().split(' ')
        
    lemList(listed) #Lemmatize list to common stem words
    
    toDel = set()


    listed = [word for word in [word for word in listed if word not in stopWords] if word not in toDel] + list(toAdd) 
    
    return listed
    
    
def showWordCloud(text):
    plt.figure(figsize=(8,8)).gca()
    fontPath = '/Library/Fonts/Microsoft/'
    font = 'Verdana.ttf'
    wc = WordCloud(background_color="white", max_words=2000,font_path=fontPath+font,stopwords=['ebola','link','atweeter','user'],
                   height = 800, width = 800)
    wc.generate(text)
    plt.imshow(wc)
    plt.axis("off")
    plt.show()

def getWordWeights(dataIn,daysPast,directory, timeStamp,mode = 'image'):
    data = deepcopy(dataIn['data'])
    dates = [parser.parse(entry['created_at']) for index,entry in data.iterrows()]
    rightBound = max(dates)
    leftBound = rightBound - datetime.timedelta(days = daysPast)
    data = [entry for index,entry in data.iterrows() if leftBound < parser.parse(entry['created_at']) < rightBound]
    
    if  'nlpCat' in data[0].keys():
        CatCol = 'nlpCat'
    elif 'nltkCat' in data[0].keys():
        CatCol = 'nltkCat'
    else:
        CatCol = 'tweetType'
    
    wordList = dict()
    
    if mode == 'image':
        wordList['all'] = [prepTweet(entry['text']) for entry in data]
        
        cats = set([entry[CatCol] for entry in data])
        for cat in cats:
            wordList[cat] = [prepTweet(entry['text']) for entry in data if entry[CatCol] == cat]
        cats.add('all')
        for cat in cats:
            wordList[cat] = ' '.join([' '.join([word.split("'")[0] for word in entry if word not in blockKeys]) for entry in wordList[cat]]) 
        return wordList
        
    elif mode != 'image':    
        wordWeights = dict()
        wordCloud = []
        wordList['all'] = [prepTweet(entry['text']) for entry in data] 
    
        cats = set([entry[CatCol] for entry in data])
        for cat in cats:
            wordList[cat] = [prepTweet(entry['text']) for entry in data if entry[CatCol] == cat] 
    
        cats.add('all')
        for cat in cats:
            wordList[cat] = [[word.split("'")[0] for word in entry if word not in blockKeys] for entry in wordList[cat]]
        
        
        for cat in cats:
            wordWeights[cat] = dict()  
            for tweet in wordList[cat]:
                for word in tweet:
                    if word not in wordWeights[cat].keys():
                        wordWeights[cat][word] = 1
                    else:
                        wordWeights[cat][word] += 1
                        
        for cat in cats:
            listed = []
            for key in wordWeights[cat].keys():
                listed.append('{text: "%s", weight: %s}' % (str(key),wordWeights[cat][key]))
            wordCloud.append('{%s: [%s]}' % (cat,', '.join(listed)))
        
    jsonOut = '{wordcloud: [%s]}' % ', '.join(wordCloud)
    outName = "wordcloud.json"
    print "Writing wordcloud to '"+outName + "'"
    
    outFile = open(directory+outName, "w")
    outFile.write(jsonOut)
    outFile.close()
    return directory+outName