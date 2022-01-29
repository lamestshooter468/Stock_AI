from flask import Flask, render_template  # , request          <----  uncomment to request for method below

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
    return render_template('viewStock.html')




if __name__ == '__main__':
    app.run(debug = True)
