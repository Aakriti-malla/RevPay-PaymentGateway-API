from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Welcom to Rev Pay"

if __name__ is '__main__':
    app.run()