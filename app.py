from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Flaskアプリ起動成功！</h1>
    <p>Renderへのデプロイ成功</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)