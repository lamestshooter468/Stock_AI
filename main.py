import datetime
from importlib.metadata import metadata
from multiprocessing import connection
from time import strftime
from flask import Flask, jsonify, render_template,redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from newsapi.newsapi_client import NewsApiClient
from dateutil.relativedelta import relativedelta
import pandas as pd
import ctypes
from sklearn import semi_supervised  # An included library with Python install. 
import sqlalchemy as db
from flair.models import TextClassifier
from flair.data import Sentence
app = Flask(__name__)
engine = db.create_engine('mysql://admin:eu866WCm6ipb@112.199.252.164:3306/ai_project')
connection = engine.connect()
metadata = db.MetaData()
news_table = db.Table('tbl_news', metadata, autoload=True, autoload_with=engine)
import requests
import os
import shelve
import json
import calendar
from datetime import datetime, timezone
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import models.loadmodels as loadmodels

import config

app = Flask(__name__)
app.secret_key = "AI STOCK PROJECT"


# ------------------Navigation---------------------
@app.route('/', methods=["GET"])
def home():
    return render_template('Home.html')
    # render_template('Home.html', html_var_name=var_1))  to parse information over to html


@app.route('/aboutUs', methods=["GET"])
def aboutUs():
    return render_template('aboutUs.html')


@app.route('/ourService', methods=["GET"])
def ourService():
    return render_template('ourService.html')


# ------------------News---------------------
@app.route('/viewNews', methods=["GET"])
def viewNews():
    try:
        db = shelve.open('articles.db', "r")
        articles = db["articles"]
        db.close()
    except:
        articles = {}
    return render_template('viewNews.html', articles=articles)


# -----------------admin----------------
api_key = os.getenv("NEWS_API")
newsapi = NewsApiClient(api_key=config.api_key)


@app.route('/admin', methods=["GET"])
def adminLogin():
    if session.get("admin"):
        return redirect(url_for('adminNews'))
    wrongPassword = request.args.get('wrongPassword')
    return render_template('adminLogin.html', wrongPassword=wrongPassword)


@app.route('/admin/check', methods=["POST"])
def adminLoginCheck():
    data = request.form
    print(data)
    if data["username"] == "admin" and data["password"] == "123":
        session["admin"] = True
        return redirect(url_for('adminNews'))
    else:
        return redirect(url_for('adminLogin', wrongPassword=True))


@app.route('/admin/logout', methods=["POST", "GET"])
def adminLogout():
    session["admin"] = False
    return redirect(url_for('home'))


@app.route('/admin/news', methods=["GET"])
def adminNews():
    if session.get("admin"):
        try:
            db = shelve.open('articles.db', "r")
            articles = db["articles"]
            db.close()
        except:
            articles = {}
        return render_template('adminNews.html', articles=articles)
    else:
        return redirect(url_for('adminLogin'))


@app.route('/admin/refreshNews', methods=["POST"])
def adminRefreshNews():
    if session.get("admin"):
        btc_articles = newsapi.get_everything(q='bitcoin',
                                              language='en',
                                              sort_by='publishedAt',
                                              page=1)
        articles = btc_articles["articles"]
        for article in articles:
            del article["author"]
            del article["description"]
            del article["source"]
            del article["urlToImage"]
            text = requests.post("http://127.0.0.1:3000/predict", json={"text": article["title"]}).text.replace("'",
                                                                                                                '"')
            data = json.loads(text)
            predictedImpact = data["predicted"] + " (Confidence: " + "{:.2f}".format((data["confidence"] * 100)) + "%)"
            article["predictedImpact"] = predictedImpact

        db = shelve.open('articles.db', "c")
        db["articles"] = articles
        db.close()

        return redirect(url_for('adminNews'))
    else:
        return redirect(url_for('adminLogin'))


# -------------------------template_filter----------------------
@app.template_filter()
def month_name(month_number):
    return calendar.month_name[int(month_number)]


@app.template_filter()
def timeAgo(datetimestring):
    difference = datetime.now(timezone.utc) - datetime.fromisoformat(datetimestring[:-1] + '+00:00')
    if difference.days > 0:
        return str(difference.days) + " day"
    differentInMinutes = difference.seconds // 60
    if differentInMinutes < 60:
        return str(differentInMinutes) + " min"
    return str(differentInMinutes // 60) + " hour"


# ------------------Stock---------------------

@app.route('/viewStock', methods=["GET"])
def viewStock():
    model = loadmodels.load_arima()

    test = []
    test.append([0.51719459, 0.50692998, 0.51702329, 0.4885569, 0.54519537])
    test = np.array(test)
    preds = []

    for i in range(5):
        t_forecast = []
        t_forecast.append(model.predict(n_periods=len([test[0][i:i + 5]]), X=[test[0][i:i + 5]]))
        t_forecast = np.array(t_forecast)
        test = np.concatenate((test, np.array(t_forecast)), axis=1)
        preds.append(t_forecast[0])
    # preds = scaler.inverse_transform(preds)
    # preds = scaler.inverse_transform(test)
    return render_template('viewStock.html', values=test, max=200, labels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

@app.route('/admin_addNews', methods = ['POST', 'GET'])
def admin_addNews():
   
    return render_template('admin_addNews.html')
#background process happening without any refreshing
@app.route('/background_process_test')
def background_process_test():
     # Init
    newsapi = NewsApiClient(api_key='4d0eb542e2ca44a9af95172bad7d0221')
    # /v2/everything
    today_date = datetime.today().strftime('%Y-%m-%d')
    three_months = datetime.today() + relativedelta(months=-1)
    for page in range(1,2):
        all_articles = newsapi.get_everything(q='bitcoin',
                                        
                                        from_param=three_months,
                                        to=today_date,
                                        language='en',
                                        sort_by='relevancy',
                                        
                                        page=page)
        print(all_articles['articles'][0]['title'])
        df = pd.DataFrame(columns = ['Title', 'Author','Description','Url','PublishedAt','Content'])
        
        for i in range(len(all_articles['articles'])):
            
            title = all_articles['articles'][i]['title']

            author = all_articles['articles'][i]['author']
            description = all_articles['articles'][i]['description']
            url = all_articles['articles'][i]['url']
            publishedAt = all_articles['articles'][i]['publishedAt']
            
            content = all_articles['articles'][i]['content']
            
            #OurNewDateFormat =  datetime.datetime.strptime  (publishedAt, '%Y-%m-%dT%H:%M:%SZ')
            #new_date = datetime.date.strftime(OurNewDateFormat,'%Y-%m-%d')
            #print(new_date)
            classifier = TextClassifier.load('sentiment')
            sentence = Sentence(description)
            classifier.predict(sentence)

            values_list = [{'news_title':title,'news_description':description,'news_url':url,'publishedAt':publishedAt,'news_content':content,'news_author':author,'news_sentiment':sentence.labels[0].value,'news_score':sentence.labels[0].score }]
            query = db.insert(news_table)
            ResultProxy = connection.execute(query,values_list)


    #print(news_table.columns.keys())
    results = connection.execute(db.select([news_table])).fetchall()
    df = pd.DataFrame(results)
    
    #df.columns = results[0].keys()
    #df.head(4)
    return "Prediction Completed"
@app.route('/viewLSTM', methods=["GET"])
def viewLSTM():
    model = loadmodels.LSTMModel()

    test = []
    test.append([[0.71482802], [0.71745348], [0.66760452], [0.66274593], [0.61612082]])
    preds = []

    for i in range(5):
        test_temp = [test[0][i:i + 5]]
        test_temp = np.array(test_temp)
        test_temp = np.reshape(test_temp, (test_temp.shape[0], test_temp.shape[1], -1))
        t_forecast = model.predict(test_temp)
        t_forecast = np.array(t_forecast)
        t_forecast = np.reshape(t_forecast, (t_forecast.shape[0], t_forecast.shape[1], -1))
        test = np.column_stack((test, t_forecast))
        preds.append(t_forecast[0])
    # y_te = scaler.inverse_transform(y_te)
    # preds = scaler.inverse_transform(preds)
    print(test)
    return render_template("viewLSTM.html", values=test, labels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])


@app.route('/viewFlairNews')
def viewFlairNews():

    results = connection.execute(db.select([news_table])).fetchall()
    
    return render_template('viewFlairNews.html',results=results)

@app.route('/predict_Flair', methods = ['POST', 'GET'])
def predict_Flair():
    input = request.json['text']
    print(input)

    classifier = TextClassifier.load('sentiment')
    sentence = Sentence(input)
    classifier.predict(sentence)
    
    data = {'sentiment': sentence.labels[0].value,'score':sentence.labels[0].score}
    return jsonify(data)
if __name__ == '__main__':
    
    app.run(host='0.0.0.0',debug = True)
