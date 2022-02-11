from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world_web():
    return "Web string"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)
