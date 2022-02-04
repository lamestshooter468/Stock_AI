import pickle

import numpy
from keras.models import load_model

def LSTMModel( ):
    model=load_model("models/LSTMModel.h5")
    return model

def load_arima():
    with open("models/arima_model.pkl", "rb") as pkl:
        model = pickle.load(pkl)
        return model
