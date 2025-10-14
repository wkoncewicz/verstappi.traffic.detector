from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/message', methods=['GET'])
def message():
    return jsonify({"message": "Don't honk in the woods"}), 200

if __name__ == '__main__':
    app.run(port=5000)

