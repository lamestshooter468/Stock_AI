from flask import Flask, render_template  # , request          <----  uncomment to request for method below

app = Flask(__name__)


@app.route('/', methods=["GET"])
def home():
    return render_template('Home.html')
    # render_template('Home.html', html_var_name=var_1))  to parse information over to html


if __name__ == '__main__':
    app.run()
