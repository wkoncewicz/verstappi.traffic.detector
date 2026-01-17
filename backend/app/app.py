from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from mongo_connect import readFromDataBase, mongo_connect
from ownLogger import saveLog
from uuid6 import uuid7
app = Flask(__name__)
CORS(app)

service = {
    'name': "BACKEND",
    'info': "INFO",
    'error' : "ERROR",
    'warning': "WARNING"
}

# TODO rozdzielic kazdy endpoint do innego pliku

@app.route('/message', methods=['GET'])
def message():
    tx_id = str(uuid7())
    try:
        saveLog(service['name'],service['info'],f'/message granted',tx_id)
        return jsonify({"message": "Don't honk in the woods"}), 200
    except Exception as e:
        saveLog(service['name'],service['error'],f'/message not granted',tx_id)

@app.route('/getDataBaseData',methods=["GET"])
def getData():
    tx_id = str(uuid7())
    try:
        tokenData = request.headers.get("Authorization")
        if tokenData is None:
            saveLog(service['name'],service['error'],f'User unknown requested data from DB but failed due to the lack of token',tx_id)
            return jsonify({"error": "Token is missing"}), 401
        dataBaseData = readFromDataBase(tx_id)
        if not dataBaseData:
            saveLog(service['name'],service['error'],f'User {tokenData} requested data from DB but failed due to DB error',tx_id)
        saveLog(service['name'],service['info'],f'User {tokenData} is requesting data from DB',tx_id)
        return jsonify({"data":dataBaseData})
    except Exception as e:
        saveLog(service['name'],service['error'],str(e),tx_id)
        return jsonify({"error":"An error occured"}), 500
    
@app.route('/dhitw',methods=['GET'])
def dhitw():
    return send_file("./public/sarnaLICENCJAT.png", mimetype='image/png')

if __name__ == '__main__':
    mongo_connect()
    app.run(host='0.0.0.0', port=5000)

