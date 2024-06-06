from werkzeug.urls import url_quote
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return '@LazyDeveloper'


if __name__ == "__main__":
    app.run()
