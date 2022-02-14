from flask import Flask, request   
import gensim
import tensorflow as tf
import nltk
import numpy as np
from pattern.text.en import lemma
from flask_cors import CORS, cross_origin
import json

nltk.download('stopwords')

STOPWORDS = nltk.corpus.stopwords.words('english')
wordToReplace = {
    "crypto": "cryptocurrency",
    "ether": "ethereum"
}

def preprocess(sentence):
    
    sentence = sentence.lower()
    sentence = gensim.utils.simple_preprocess(sentence)
  
    sentence = [word for word in sentence if word not in STOPWORDS]
    
    for i in range(len(sentence)):
        word = sentence[i]
        if word in wordToReplace:
            word = wordToReplace[word]
        try:
            sentence[i] = lemma(word)
        except:
            sentence[i] = lemma(word)
    sentence = " ".join(sentence)
    return sentence

modelOptimal = tf.keras.models.load_model('modelOptimal')
CLASS_NAME = ["Decrease","Neutral","Increase"]

def predict(sentence):
    if len(preprocess(sentence)) == 0:
        return str({"predicted": CLASS_NAME[1],"confidence":1})
    y_preds = modelOptimal.predict([preprocess(sentence)])
    predict_class = np.argmax(y_preds, axis=1)
    return str({"predicted": CLASS_NAME[predict_class[0]],"confidence":max(y_preds[0])})


app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'


cors = CORS(app, resources={r"/predict": {"origins": "*"}})

@app.route('/predict', methods=["POST","OPTIONS"])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def predictAPI():
    data = request.get_json(force=True)
    return predict(data["text"])

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug = False, port=3000)



