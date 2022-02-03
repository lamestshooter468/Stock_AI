from flask import Flask, render_template  # , request          <----  uncomment to request for method below
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import models.loadmodels as loadmodels

app = Flask(__name__)


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


@app.route('/viewLSTM', methods=["GET"])
def viewLSTM():
    model = loadmodels.LSTMModel()

    test = []
    test.append([[0.71482802], [0.71745348], [0.66760452], [0.66274593], [0.61612082]])
    preds = []

    for i in range(5):
        test_temp = []
        test_temp = [test[0][i:i + 5]]
        test_temp = np.array(test_temp)
        test_temp = np.reshape(test_temp, (test_temp.shape[0], test_temp.shape[1], -1))
        t_forecast = model.predict(test_temp)
        t_forecast = np.array(t_forecast)
        t_forecast = np.reshape(t_forecast, (t_forecast.shape[0], t_forecast.shape[1], -1))
        test = np.column_stack((test, t_forecast))
        preds.append(t_forecast[0])
    # y_te = scaler.inverse_transform(y_te)
    #preds = scaler.inverse_transform(preds)
    print(test)
    return render_template("viewLSTM.html", values=test, labels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])


if __name__ == '__main__':
    app.run(debug=True)
