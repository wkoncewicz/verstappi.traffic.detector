import os
from datetime import datetime
import requests



DETECTOR_TOKEN = "tajnehaslodetectora"


def _serialize_payload(payload: dict) -> dict:
	data = dict(payload)
	ts = data.get("timeStamp")
	if isinstance(ts, datetime):
		data["timeStamp"] = ts.isoformat()
	return data


def send_traffic(payload: dict) -> bool:
	parsed_payload = {
		"timeStamp": payload.get("timeStamp"),
		"carsIn": payload.get("carIn", 0),
		"carsOut": payload.get("carOut", 0),
		"motorcyclesIn": payload.get("motorcycleIn", 0),
		"motorcyclesOut": payload.get("motorcycleOut", 0),
		"busesIn": payload.get("busIn", 0),
		"busesOut": payload.get("busOut", 0),
		"trucksIn": payload.get("truckIn", 0),
		"trucksOut": payload.get("truckOut", 0),
    }
	url = f"https://verstappi.pl:31514/api/traffic"
	data = _serialize_payload(parsed_payload)
	print(data)
	try:
		headers = {}
		headers["X-Detector-Token"] = DETECTOR_TOKEN
		resp = requests.post(url, json=data, headers=headers, verify=False)
		if resp.ok:
			return True
		print(f"Failed to send traffic: {resp.status_code} {resp.text}")
	except Exception as e:
		print(f"Failed to send traffic: {e}")
	return False