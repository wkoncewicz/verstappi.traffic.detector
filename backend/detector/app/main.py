from ultralytics import YOLO
# import cv2
import time
import argparse
# from collections import defaultdict
from datetime import datetime

# choose reader type: 'vlc' or 'ffmpeg'
from mongo_connect import saveToDataBase, mongo_connect
from stream_reader import VLCStreamReader
from ffmpeg_reader import FFmpegStreamReader

def round_down_to_10_minutes(dt: datetime) -> datetime:
    return dt.replace(
        minute=(dt.minute // 10) * 10,
        second=0,
        microsecond=0
    )
mongo_connect()
parser = argparse.ArgumentParser()
parser.add_argument("--reader", choices=["vlc", "ffmpeg"], default="vlc")
parser.add_argument("--url", type=str, required=False)
args = parser.parse_args()

stream_url = "https://wzmedia.dot.ca.gov/D3/99_JCT162E_BUT99_NB.stream/chunklist_w646513265.m3u8"
# https://wzmedia.dot.ca.gov/D3/99_JCT162E_BUT99_NB.stream/chunklist_w646513265.m3u8


if args.reader == "vlc":
    print("Using VLCStreamReader")
    reader = VLCStreamReader(stream_url, width=1280, height=720, cache_ms=2500, interval=0.03, deque_size=5)
else:
    print("Using FFmpegStreamReader")
    reader = FFmpegStreamReader(stream_url, width=1280, height=720, fps=25, queue_size=3)

model = YOLO("yolov8m.pt")

print("Model loaded")

last_position = {}
allowed = [2, 3, 5, 7]
lane_a = (557, 322)
lane_b = (1229, 425)
lane_mid_y = (lane_a[1] + lane_b[1]) // 2
max_x = 500

vehicles = {
    "timeStamp": None,
    "carIn":0, "carOut":0, "carIds": set(),
    "motorcycleIn":0, "motorcycleOut":0, "motorcycleIds": set(),
    "busIn":0, "busOut":0, "busIds": set(),
    "truckIn":0, "truckOut":0, "truckIds": set()
}
vehiclesId = {2:"car", 3:"motorcycle", 5:"bus", 7:"truck"}

fps_smooth = None
t0 = time.time()
frame_count = 0
last_csv_time = time.time()
last_db_save = time.time()

try:
    while True:
        frame = reader.get_frame()
        if frame is None:
            print("Brak klatki — czekam...")
            time.sleep(0.1)
            continue

        # frame is BGR for both readers
        results = model.track(frame, persist=True, classes=[2,3,5,7], conf=0.3, verbose=False)
        dets = results[0].boxes
        drawn = results[0].orig_img.copy()

        for box in dets:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            track_id = int(box.id[0]) if (hasattr(box, "id") and box.id is not None) else -1

            if cls not in vehiclesId:
                continue

            vehicle = vehiclesId[cls]
            vehicleIn_key = f"{vehicle}In"
            vehicleOut_key = f"{vehicle}Out"
            vehicleIds_key = f"{vehicle}Ids"

            mid_x, mid_y = (x1+x2)//2, (y1+y2)//2

            if track_id in last_position and cls in allowed and mid_x > max_x:
                last_x, last_y = last_position[track_id]

                if mid_y > lane_mid_y > last_y:
                    if track_id not in vehicles[vehicleIds_key]:
                        vehicles[vehicleIn_key] += 1
                        vehicles[vehicleIds_key].add(track_id)
                        print("Vehicle detected")

                elif mid_y < lane_mid_y < last_y:
                    if track_id not in vehicles[vehicleIds_key]:
                        vehicles[vehicleOut_key] += 1
                        vehicles[vehicleIds_key].add(track_id)
                        print("Vehicle detected")

            last_position[track_id] = (mid_x, mid_y)

            label = f"{model.names[cls]} id={track_id} conf={conf:.2f}"
        #     cv2.rectangle(drawn, (x1, y1), (x2, y2), (0,255,0), 2)
        #     cv2.circle(drawn, (mid_x, mid_y), 5, (0,0,255), -1)
        #     cv2.putText(drawn, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        # Label_in = f"Vehicles in: {vehicles['carIn']+vehicles['motorcycleIn']+vehicles['busIn']+vehicles['truckIn']}"
        # Label_out = f"Vehicles out: {vehicles['carOut']+vehicles['motorcycleOut']+vehicles['busOut']+vehicles['truckOut']}"
        # cv2.line(drawn, lane_a, lane_b, (0,0,255), 2)
        # cv2.putText(drawn, Label_in, (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
        # cv2.putText(drawn, Label_out, (300,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

        # cv2.imshow("Detections", drawn)
        # if cv2.waitKey(1) & 0xFF == 27:
        #     break

        # FPS counting
        frame_count += 1
        if frame_count % 5 == 0:
            now = time.time()
            dt = now - t0
            fps = 5.0 / dt if dt>0 else 0.0
            fps_smooth = fps if fps_smooth is None else (0.7*fps_smooth + 0.3*fps)
            t0 = now
            print(f"FPS: {fps_smooth:.1f}")
            czas = round_down_to_10_minutes(datetime.now())
            if vehicles["timeStamp"] is None:
                vehicles["timeStamp"] = czas

            if vehicles["timeStamp"] != czas:
                saveToDataBase(vehicles)
                vehicles = {
                    "timeStamp": czas,
                    "carIn":0, "carOut":0, "carIds": set(),
                    "motorcycleIn":0, "motorcycleOut":0, "motorcycleIds": set(),
                    "busIn":0, "busOut":0, "busIds": set(),
                    "truckIn":0, "truckOut":0, "truckIds": set()
                }

                
finally:
    reader.stop()
    # cv2.destroyAllWindows()
