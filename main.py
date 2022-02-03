from flask import Flask, render_template, redirect, url_for, request, session    
from newsapi import NewsApiClient
import requests
import os
import shelve
import json
import calendar
from datetime import datetime, timezone

import config

app = Flask(__name__)
app.secret_key = "AI STOCK PROJECT"

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


@app.route('/viewNews', methods=["GET"])
def viewNews():
    try:
        db = shelve.open('articles.db', "r")
        articles = db["articles"]
        db.close()
    except:
        articles = {}
    return render_template('viewNews.html',articles=articles)


@app.route('/viewStock', methods=["GET"])
def viewStock():
    return render_template('viewStock.html')

# -----------------admin----------------
api_key = os.getenv("NEWS_API")
newsapi = NewsApiClient(api_key=config.api_key)

@app.route('/admin', methods=["GET"])
def adminLogin():
    if session.get("admin"):
        return redirect(url_for('adminNews'))
    wrongPassword = request.args.get('wrongPassword')
    return render_template('adminLogin.html',wrongPassword=wrongPassword)


@app.route('/admin/check', methods=["POST"])
def adminLoginCheck():
    data = request.form
    print(data)
    if data["username"] == "admin" and data["password"] == "123":
        session["admin"] = True
        return redirect(url_for('adminNews'))
    else:
        return redirect(url_for('adminLogin', wrongPassword=True))

@app.route('/admin/logout', methods=["POST","GET"])
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
        return render_template('adminNews.html',articles=articles)
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
            text = requests.post("http://127.0.0.1:3000/predict", json = {"text": article["title"]}).text.replace("'",'"')
            data = json.loads(text)
            predictedImpact = data["predicted"] + " (Confidence: "+ "{:.2f}".format((data["confidence"]*100)) + "%)"
            article["predictedImpact"] = predictedImpact

        db = shelve.open('articles.db', "c")
        db["articles"] = articles
        db.close()

        return redirect(url_for('adminNews'))
    else:
        return redirect(url_for('adminLogin'))


#-------------------------template_filter----------------------
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
    return str(differentInMinutes//60) + " hour"


if __name__ == '__main__':
    app.run(debug = True)
