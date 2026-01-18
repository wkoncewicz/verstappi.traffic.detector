from datetime import datetime
import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from mongo_connect import readFromDataBase, mongo_connect,saveLog
from uuid6 import uuid7
from mongo_models import traffic as traffic_model

app = Flask(__name__)
CORS(app)

service = {
    'name': "[BACKEND]",
    'info': "INFO",
    'error' : "ERROR",
    'warning': "WARNING"
}

DETECTOR_TOKEN = os.getenv("DETECTOR_TOKEN") or "tajnehaslodetectora"

@app.route('/traffic', methods=['POST'])
def post_traffic():
    tx_id = str(uuid7())
    try:
        if not DETECTOR_TOKEN:
            saveLog(service['name'], service['warning'], "/traffic DETECTOR_TOKEN not set", tx_id)
            return jsonify({"error": "Server not configured"}), 500

        token = request.headers.get("X-Detector-Token")
        if token != DETECTOR_TOKEN:
            saveLog(service['name'], service['warning'], "/traffic invalid token", tx_id)
            return jsonify({"error": "Unauthorized"}), 401

        payload = request.get_json(force=True) or {}
        required = [
            "timeStamp",
            "carIn", "carOut",
            "motorcycleIn", "motorcycleOut",
            "busIn", "busOut",
            "truckIn", "truckOut",
        ]
        missing = [k for k in required if k not in payload]
        if missing:
            saveLog(service['name'], service['error'], f"/traffic missing fields: {missing}", tx_id)
            return jsonify({"error": "Missing fields", "missing": missing}), 400

        data = traffic_model.Traffic(
            time=datetime.fromisoformat(payload["timeStamp"]),
            carsIn=int(payload["carIn"]),
            carsOut=int(payload["carOut"]),
            motorcyclesIn=int(payload["motorcycleIn"]),
            motorcyclesOut=int(payload["motorcycleOut"]),
            busesIn=int(payload["busIn"]),
            busesOut=int(payload["busOut"]),
            trucksIn=int(payload["truckIn"]),
            trucksOut=int(payload["truckOut"]),
        )
        data.save()
        saveLog(service['name'], service['info'], "/traffic saved", tx_id)
        return jsonify({"status": "ok"}), 201
    except Exception as e:
        saveLog(service['name'], service['error'], str(e), tx_id)
        return jsonify({"error": f"An error occured {e}"}), 500

@app.route('/message', methods=['GET'])
def message():
    tx_id = str(uuid7())
    try:
        saveLog(service['name'],service['info'],f'/message granted',tx_id)
        return jsonify({"message": "Don't honk in the woods"}), 200
    except Exception as e:
        saveLog(service['name'],service['error'],f'/message not granted',tx_id)
        return jsonify({"error": f"An error occured {e}"}), 500
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
        return jsonify({"error": f"An error occured {e}"}), 500
    
@app.route('/dhitw',methods=['GET'])
def dhitw():
    return send_file("./public/sarnaLICENCJAT.png", mimetype='image/png')

mongo_connect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

