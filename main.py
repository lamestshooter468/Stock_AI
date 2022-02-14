import datetime
from urllib import response
from importlib_metadata import metadata
from multiprocessing import connection
from time import strftime
from flask import Flask, jsonify, render_template, redirect, url_for, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from newsapi.newsapi_client import NewsApiClient
from dateutil.relativedelta import relativedelta
import pandas as pd
import ctypes
from sklearn import semi_supervised  # An included library with Python install. 
import sqlalchemy as db
from flair.models import TextClassifier
from flair.data import Sentence
import requests
import os
import shelve
import json
import calendar
from datetime import datetime, timezone
import numpy as np
import pandas_datareader as web
from sklearn.preprocessing import MinMaxScaler
import models.loadmodels as loadmodels

import config

app = Flask(__name__)
CORS(app)
engine = db.create_engine('mysql://admin:eu866WCm6ipb@112.199.252.164:3306/ai_project')
connection = engine.connect()
metadata = db.MetaData()
news_table = db.Table('tbl_news', metadata, autoload=True, autoload_with=engine)
stock_table = db.Table('tbl_stock_price', metadata, autoload=True, autoload_with=engine)
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
        articlesRelevancy = db["articlesRelevancy"]
        db.close()
    except:
        articles = {}
        articlesRelevancy = {}
    return render_template('viewNews.html',articles=articles, articlesRelevancy=articlesRelevancy)

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
            articlesRelevancy = db["articlesRelevancy"]
            db.close()
        except:
            articles = {}
            articlesRelevancy = {}
        return render_template('adminNews.html',articles=articles, articlesRelevancy=articlesRelevancy)
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

        btc_articlesByRelevany = newsapi.get_everything(q='bitcoin',
                                        language='en',
                                        sort_by='relevancy',
                                        page=1)
        articlesByRelevany = btc_articlesByRelevany["articles"]
        for article in articlesByRelevany:
            del article["author"]
            del article["description"]
            del article["source"]
            del article["urlToImage"]
            text = requests.post("http://127.0.0.1:3000/predict", json = {"text": article["title"]}).text.replace("'",'"')
            data = json.loads(text)
            predictedImpact = data["predicted"] + " (Confidence: "+ "{:.2f}".format((data["confidence"]*100)) + "%)"
            article["predictedImpact"] = predictedImpact

        db = shelve.open('articles.db', "c")
        db["articlesRelevancy"] = articlesByRelevany
        db.close()

        return redirect(url_for('adminNews'))
    else:
        return redirect(url_for('adminLogin'))

@app.route('/admin_addNews', methods=['POST', 'GET'])
def admin_addNews():
    return render_template('admin_addNews.html')


#---------------------------Feedback----------------------------
@app.route('/aboutUs/submitForm', methods=["POST"])
def submitFeedback():
    try:
        db = shelve.open('feedback.db', "r")
        feedbackdb = db["feedback"]
        db.close()
    except:
        feedbackdb = []
    feedback = {}
    feedback["feedbackHeading"] = request.form["feedbackHeading"]
    feedback["feedbackComment"] = request.form["feedbackComment"]
    feedback["utctime"] = str(datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    feedbackdb.append(feedback)
    db = shelve.open('feedback.db', "c")
    db["feedback"] = feedbackdb
    db.close()

    return redirect(url_for('aboutUs'))

@app.route('/admin/feedback', methods=["GET"])
def adminFeedback():
    if session.get("admin"):
        try:
            db = shelve.open('feedback.db', "r")
            feedbackdb = db["feedback"]
            db.close()
        except:
            feedbackdb = []
        return render_template('adminFeedback.html',feedbackdb=feedbackdb)
    else:
        return redirect(url_for('adminLogin'))

@app.route('/feedback/clearall', methods=["POST"])
def feedbackClearall():
    if session.get("admin"):
        db = shelve.open('feedback.db', "c")
        db["feedback"] = []
        db.close()

        return redirect(url_for('adminFeedback'))
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

# ------------------API reqs---------------------

# background process happening without any refreshing
@app.route('/background_process_test')
def background_process_test():
    # Init
    newsapi = NewsApiClient(api_key='4d0eb542e2ca44a9af95172bad7d0221')
    crypto_currency = "BTC"
    against_currency = "USD"
    # /v2/everything
    today_date = datetime.today().strftime('%Y-%m-%d')
    five_days = datetime.today() + relativedelta(days=-4)
    three_months = datetime.today() + relativedelta(months=-1)
    stock_data = web.DataReader(f'{crypto_currency}-{against_currency}', "yahoo", five_days, today_date)

    for i in range(len(stock_data)):
        # dt_format = datetime.strptime(stock_data.index[i], '%Y-%m-%d%H:%M:%S')
        new_date = datetime.strftime(stock_data.index[i], '%Y-%m-%d')
        values_list = [{"stock_date": new_date, "stock_price": stock_data["Close"][i]}]
        query = db.insert(stock_table)
        ResultProxy = connection.execute(query, values_list)

    for page in range(1, 2):
        all_articles = newsapi.get_everything(q='bitcoin',
                                              from_param=three_months,
                                              to=today_date,
                                              language='en',
                                              sort_by='relevancy',
                                              page=page)
        # print(all_articles['articles'][0]['title'])
        # df = pd.DataFrame(columns=['Title', 'Author', 'Description', 'Url', 'PublishedAt', 'Content'])

        for i in range(len(all_articles['articles'])):
            title = all_articles['articles'][i]['title']

            author = all_articles['articles'][i]['author']
            description = all_articles['articles'][i]['description']
            url = all_articles['articles'][i]['url']
            publishedAt = all_articles['articles'][i]['publishedAt']

            content = all_articles['articles'][i]['content']

            # OurNewDateFormat =  datetime.datetime.strptime  (publishedAt, '%Y-%m-%dT%H:%M:%SZ')
            # new_date = datetime.date.strftime(OurNewDateFormat,'%Y-%m-%d')
            # print(new_date)
            classifier = TextClassifier.load('sentiment')
            sentence = Sentence(description)
            classifier.predict(sentence)

            values_list = [
                {'news_title': title, 'news_description': description, 'news_url': url, 'publishedAt': publishedAt,
                 'news_content': content, 'news_author': author, 'news_sentiment': sentence.labels[0].value,
                 'news_score': sentence.labels[0].score}]
            query = db.insert(news_table)
            ResultProxy = connection.execute(query, values_list)

    # print(news_table.columns.keys())
    results = connection.execute(db.select([news_table])).fetchall()
    df = pd.DataFrame(results)

    # df.columns = results[0].keys()
    # df.head(4)
    return "Prediction Completed"


# ------------------Stock---------------------

@app.route('/viewStock', methods=["GET", "POST"])
def viewStock():
    day = 5
    try:
        day = request.json["days"]
    except:
        None
    results = connection.execute(db.select([stock_table])).fetchall()
    news_result = connection.execute(db.select([news_table])).fetchall()

    # scaler = MinMaxScaler(feature_range=(0, 1)
    # scaled_data = scaler.fit_transform([result[1] for result in results].reshape(-1, 1))

    labels = [str(result[0]) for result in results]
    labels = labels + [str(datetime.strftime((datetime.today() + relativedelta(days=i)), '%Y-%m-%d')) for i in range(0, day)]

    model = loadmodels.load_arima()

    test = []
    test.append([result[1] for result in results])
    # test.append([data for data in scaled_data])
    test = np.array(test)
    preds = []

    for i in range(day):
        t_forecast = []
        t_forecast.append(model.predict(n_periods=len([test[0][i:i + 5]]), X=[test[0][i:i + 5]]))
        t_forecast = np.array(t_forecast)
        test = np.concatenate((test, np.array(t_forecast)), axis=1)
        preds.append(t_forecast[0])
    # preds = scaler.inverse_transform(preds)
    # preds = scaler.inverse_transform(test)

    result = round((test[0][-1] - test[0][4]) / test[0][4], 3)
    if request.method == "POST":
        data = {"values": test.tolist(), "labels": labels, "result": result}
        data = jsonify(data)
        data.headers.add("Access-Control-Allow-Origin", '*')
        return data

    return render_template('viewStock.html', values=test.tolist(), max=200, labels=labels, result=result, news_result=news_result)



@app.route('/viewLSTM', methods=["GET", "POST"])
def viewLSTM():
    day = 5
    try:
        day = request.json["days"]
    except:
        None
    results = connection.execute(db.select([stock_table])).fetchall()
    news_result = connection.execute(db.select([news_table])).fetchall()

    model = loadmodels.LSTMModel()

    labels = [str(result[0]) for result in results]
    labels = labels + [str(datetime.strftime((datetime.today() + relativedelta(days=i)), '%Y-%m-%d')) for i in range(0, day)]
    #print(labels)

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(np.array([result[1] for result in results]).reshape(-1, 1))

    test = [result for result in scaled_data]
    test=np.array(test)
    #print(test)
    
    preds = []

    for i in range(day):
        test_temp = [test[i:i + 5]]
        #print(test_temp)
        test_temp = np.array(test_temp)
        test_temp = np.reshape(test_temp, (test_temp.shape[0], test_temp.shape[1], -1))
        #print(test_temp.shape)

        t_forecast = model.predict(test_temp)
        t_forecast = np.array(t_forecast)
        #t_forecast = np.reshape(t_forecast, (t_forecast.shape[0], t_forecast.shape[1], -1))
        #print(test.shape , "\n\n", t_forecast.shape)
        test = np.r_[test, t_forecast]
        preds.append(t_forecast[0])
    # y_te = scaler.inverse_transform(y_te)
    test = scaler.inverse_transform(test)
    test = test.tolist()
    result = round((test[-1][0] - test[4][0]) / test[4][0], 3)

    if request.method == "POST":
        data = {"values": test, "labels": labels, "result": result}
        data = jsonify(data)
        data.headers.add("Access-Control-Allow-Origin", '*')
        return data

    return render_template("viewLSTM.html", values=test, max=200, labels=labels, result=result, news_result=news_result)


@app.route('/viewFlairNews')
def viewFlairNews():
    results = connection.execute(db.select([news_table])).fetchall()

    return render_template('viewFlairNews.html', results=results)


@app.route('/predict_Flair', methods=['POST', 'GET'])
def predict_Flair():
    input = request.json['text']
    print(input)

    classifier = TextClassifier.load('sentiment')
    sentence = Sentence(input)
    classifier.predict(sentence)

    data = {'sentiment': sentence.labels[0].value, 'score': sentence.labels[0].score}
    return jsonify(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
