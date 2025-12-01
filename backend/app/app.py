from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
app = Flask(__name__)
CORS(app)



# TODO rozdzielic kazdy endpoint do innego pliku

@app.route('/message', methods=['GET'])
def message():
    return jsonify({"message": "Don't honk in the woods"}), 200

@app.route('/getDBData',methods=["GET"])
def getDayData():
    return jsonify({"DBData":"TODO"})

@app.route('/getCameraImage',methods=['GET'])
def getCameraImage():
    return jsonify({"CamImage":"TODO"})

@app.route('/dhitw',methods=['GET'])
def dhitw():
    return send_file("./public/sarnaLICENCJAT.png", mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

