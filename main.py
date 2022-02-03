from flask import Flask, render_template  # , request          <----  uncomment to request for method below
import pickle
import numpy as np
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)


scaler = MinMaxScaler(feature_range=(0, 1))
arr = np.array([[0.51719459, 0.50692998, 0.51702329, 0.4885569, 0.54519537]])
data = scaler.fit(X=arr.reshape(-1, 1))


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
    return render_template('viewNews.html')


@app.route('/viewStock', methods=["GET"])
def viewStock():
    with open("models/arima_model.pkl", "rb") as pkl:
        model = pickle.load(pkl)

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
        #preds = scaler.inverse_transform(preds)
        preds = scaler.inverse_transform(test)
        return render_template('viewStock.html', values=preds, max=200, labels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])


if __name__ == '__main__':
    app.run(debug=True)
