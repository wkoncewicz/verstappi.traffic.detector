from datetime import datetime, timedelta, time
import os

from dateutil.relativedelta import relativedelta
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

def split_to_months(days):
    months = {}

    for day in days:
        month_key = day.strftime("%Y-%m")
        if month_key not in months:
            months[month_key] = {}
        
        keys = day.keys()
        for key in keys:
            if key == "timeStamp":
                continue
            if key not in months[month_key]:
                months[month_key][key] = 0
            months[month_key][key] += day[key]
    return months

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
            "carsIn", "carsOut",
            "motorcyclesIn", "motorcyclesOut",
            "busesIn", "busesOut",
            "trucksIn", "trucksOut",
        ]
        missing = [k for k in required if k not in payload]
        if missing:
            saveLog(service['name'], service['error'], f"/traffic missing fields: {missing}", tx_id)
            return jsonify({"error": "Missing fields", "missing": missing}), 400
        
        timeStamp = datetime.fromisoformat(payload["timeStamp"])

        data = traffic_model.Traffic(
            time=timeStamp,
            carsIn=int(payload["carsIn"]),
            carsOut=int(payload["carsOut"]),
            motorcyclesIn=int(payload["motorcyclesIn"]),
            motorcyclesOut=int(payload["motorcyclesOut"]),
            busesIn=int(payload["busesIn"]),
            busesOut=int(payload["busesOut"]),
            trucksIn=int(payload["trucksIn"]),
            trucksOut=int(payload["trucksOut"]),
        )
        data.save()

        if timeStamp.time() == time(0, 15, 0):
            yesterday = timeStamp - timedelta(days=1)

            dataList = traffic_model.Traffic.objects(
                time__gte=datetime(yesterday.year, yesterday.month, yesterday.day),
                time__lt=datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
            )
            total = {
                "carsIn": 0, "carsOut": 0,
                "motorcyclesIn": 0, "motorcyclesOut": 0,
                "busesIn": 0, "busesOut": 0,
                "trucksIn": 0, "trucksOut": 0,
            }
            for entry in dataList:
                total["carsIn"] += entry.carsIn
                total["carsOut"] += entry.carsOut
                total["motorcyclesIn"] += entry.motorcyclesIn
                total["motorcyclesOut"] += entry.motorcyclesOut
                total["busesIn"] += entry.busesIn
                total["busesOut"] += entry.busesOut
                total["trucksIn"] += entry.trucksIn
                total["trucksOut"] += entry.trucksOut

            dailyData = traffic_model.DailyTraffic(
                day=yesterday,
                traffic=traffic_model.TrafficData(
                    carsIn=int(total["carsIn"]),
                    carsOut=int(total["carsOut"]),
                    motorcyclesIn=int(total["motorcyclesIn"]),
                    motorcyclesOut=int(total["motorcyclesOut"]),
                    busesIn=int(total["busesIn"]),
                    busesOut=int(total["busesOut"]),
                    trucksIn=int(total["trucksIn"]),
                    trucksOut=int(total["trucksOut"]),
                )
            )
            dailyData.save()

        saveLog(service['name'], service['info'], "/traffic saved", tx_id)
        return jsonify({"status": "ok"}), 201
    except Exception as e:
        saveLog(service['name'], service['error'], str(e), tx_id)
        return jsonify({"error": f"An error occured {e}"}), 500
    
@app.route('/traffic/<year>', methods=['GET'])
def get_traffic(year):
    tx_id = str(uuid7())
    try:
        start_time = datetime(int(year), 1, 1)
        end_time = datetime(int(year) + 1, 1, 1)

        data = traffic_model.DailyTraffic.objects(
            day__gte=start_time,
            day__lt=end_time
        )

        result = []
        for entry in data:
            result.append({
                "timeStamp": entry.day.isoformat(),
                "carsIn": entry.traffic.carsIn,
                "carsOut": entry.traffic.carsOut,
                "motorcyclesIn": entry.traffic.motorcyclesIn,
                "motorcyclesOut": entry.traffic.motorcyclesOut,
                "busesIn": entry.traffic.busesIn,
                "busesOut": entry.traffic.busesOut,
                "trucksIn": entry.traffic.trucksIn,
                "trucksOut": entry.traffic.trucksOut,
            })

        splitted_result = split_to_months(result)

        saveLog(service['name'], service['info'], f"/traffic/{year} granted", tx_id)
        return jsonify({"data": splitted_result}), 200
    except Exception as e:
        saveLog(service['name'], service['error'], str(e), tx_id)
        return jsonify({"error": f"An error occured {e}"}), 500
    
@app.route('/traffic/<year>/<month>', methods=['GET'])
def get_traffic_month(year, month):
    tx_id = str(uuid7())
    try:
        start_time = datetime(int(year), int(month), 1)
        end_time = start_time + relativedelta(months=1)

        data = traffic_model.DailyTraffic.objects(
            day__gte=start_time,
            day__lt=end_time
        )

        result = []
        for entry in data:
            result.append({
                "timeStamp": entry.day.isoformat(),
                "carsIn": entry.traffic.carsIn,
                "carsOut": entry.traffic.carsOut,
                "motorcyclesIn": entry.traffic.motorcyclesIn,
                "motorcyclesOut": entry.traffic.motorcyclesOut,
                "busesIn": entry.traffic.busesIn,
                "busesOut": entry.traffic.busesOut,
                "trucksIn": entry.traffic.trucksIn,
                "trucksOut": entry.traffic.trucksOut,
            })

        saveLog(service['name'], service['info'], f"/traffic/{year}/{month} granted", tx_id)
        return jsonify({"data": result}), 200
    except Exception as e:
        saveLog(service['name'], service['error'], str(e), tx_id)
        return jsonify({"error": f"An error occured {e}"}), 500
    
@app.route('/traffic/<year>/<month>/<day>', methods=['GET'])
def get_traffic_day(year, month, day):
    tx_id = str(uuid7())
    try:
        start_time = datetime(int(year), int(month), int(day))
        end_time = start_time + timedelta(days=1)

        data = traffic_model.Traffic.objects(
            time__gte=start_time,
            time__lt=end_time
        )

        result = []
        for entry in data:
            result.append({
                "timeStamp": entry.time.isoformat(),
                "carsIn": entry.carsIn,
                "carsOut": entry.carsOut,
                "motorcyclesIn": entry.motorcyclesIn,
                "motorcyclesOut": entry.motorcyclesOut,
                "busesIn": entry.busesIn,
                "busesOut": entry.busesOut,
                "trucksIn": entry.trucksIn,
                "trucksOut": entry.trucksOut,
            })

        saveLog(service['name'], service['info'], f"/traffic/{year}/{month}/{day} granted", tx_id)
        return jsonify({"data": result}), 200
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
    
@app.route('/dhitw',methods=['GET'])
def dhitw():
    return send_file("./public/sarnaLICENCJAT.png", mimetype='image/png')

mongo_connect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

