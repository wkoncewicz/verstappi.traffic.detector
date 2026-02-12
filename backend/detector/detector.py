from ultralytics import YOLO
import cv2
import time
import argparse
from datetime import datetime

from api_sender import send_traffic
from stream_reader import VLCStreamReader
from ffmpeg_reader import FFmpegStreamReader


def round_down_to_10_minutes(dt: datetime) -> datetime:
    return dt.replace(
        minute=(dt.minute // 10) * 10,
        second=0,
        microsecond=0
    )
def round_down_to_2_minutes(dt: datetime) -> datetime:
    return dt.replace(
        minute=(dt.minute // 2) * 2,
        second=0,
        microsecond=0
    )


def get_side(mid_y, line_y):
    return "top" if mid_y < line_y else "bottom"

parser = argparse.ArgumentParser()
parser.add_argument("--reader", choices=["vlc", "ffmpeg"], default="vlc")
parser.add_argument("--url", type=str, required=False)
args = parser.parse_args()

stream_url = args.url or "https://wzmedia.dot.ca.gov/D3/99_JCT162E_BUT99_NB.stream/chunklist_w646513265.m3u8"



def create_reader():
    if args.reader == "vlc":
        return VLCStreamReader(
            stream_url,
            width=1280,
            height=720,
            cache_ms=2500,
            interval=0.03,
            deque_size=5
        )
    return FFmpegStreamReader(
        stream_url,
        width=1280,
        height=720,
        fps=25,
        queue_size=3
    )


reader = create_reader()



model = YOLO("yolov8x.pt")
model.to("cuda")



allowed_classes = [2, 3, 5, 7]
vehicles_map = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

lane_a = (557, 322)
lane_b = (1229, 425)
lane_mid_y = (lane_a[1] + lane_b[1]) // 2

max_x = 500


def empty_vehicles(ts):
    return {
        "timeStamp": ts,
        "carIn": 0, "carOut": 0,
        "motorcycleIn": 0, "motorcycleOut": 0,
        "busIn": 0, "busOut": 0,
        "truckIn": 0, "truckOut": 0,
    }



track_states = {}  # track_id -> {"side": "top/bottom", "counted": bool}




fps_smooth = None
t0 = time.time()
frame_count = 0



current_time_window = round_down_to_10_minutes(datetime.now()).isoformat()
vehicles = empty_vehicles(current_time_window)
current_two_minutes_window = round_down_to_2_minutes(datetime.now())


dead_frame_count = 0
try:
    while True:
        frame = reader.get_frame()
        if frame is None:
            print("Brak klatki — czekam...")
            time.sleep(0.1)
            dead_frame_count += 1
            if dead_frame_count >= 150:
                dead_frame_count = 0
                reader.stop()
                reader = create_reader()

            continue

        results = model.track(
            frame,
            persist=True,
            classes=allowed_classes,
            conf=0.3,
            verbose=False,
            device="cuda:0"
        )

        dets = results[0].boxes
        drawn = results[0].orig_img.copy()

        active_ids = set()

        for box in dets:
            if box.id is None:
                continue

            track_id = int(box.id[0])
            active_ids.add(track_id)

            cls = int(box.cls[0])
            if cls not in vehicles_map:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            mid_x = (x1 + x2) // 2
            mid_y = (y1 + y2) // 2

            if mid_x < max_x:
                continue

            vehicle = vehicles_map[cls]
            side = get_side(mid_y, lane_mid_y)

            # INIT
            if track_id not in track_states:
                track_states[track_id] = {
                    "side": side,
                    "counted": False
                }
            else:
                prev_side = track_states[track_id]["side"]
                counted = track_states[track_id]["counted"]

                # LINE CROSSING
                if not counted and prev_side != side:
                    if prev_side == "top" and side == "bottom":
                        vehicles[f"{vehicle}In"] += 1
                    elif prev_side == "bottom" and side == "top":
                        vehicles[f"{vehicle}Out"] += 1

                    track_states[track_id]["counted"] = True

                track_states[track_id]["side"] = side

            # DRAW
            label = f"{model.names[cls]} id={track_id}"
            cv2.rectangle(drawn, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(drawn, (mid_x, mid_y), 5, (0, 0, 255), -1)
            cv2.putText(drawn, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


        total_in = vehicles["carIn"] + vehicles["motorcycleIn"] + vehicles["busIn"] + vehicles["truckIn"]
        total_out = vehicles["carOut"] + vehicles["motorcycleOut"] + vehicles["busOut"] + vehicles["truckOut"]

        cv2.line(drawn, lane_a, lane_b, (0, 0, 255), 2)
        cv2.putText(drawn, f"Vehicles IN: {total_in}", (100, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(drawn, f"Vehicles OUT: {total_out}", (350, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow("Detections", drawn)
        if cv2.waitKey(1) & 0xFF == 27:
            break



        frame_count += 1
        if frame_count % 5 == 0:
            now = time.time()
            dt = now - t0
            fps = 5.0 / dt if dt > 0 else 0.0
            fps_smooth = fps if fps_smooth is None else (0.7 * fps_smooth + 0.3 * fps)
            t0 = now

            print(f"FPS: {fps_smooth:.1f}")
            print(vehicles)
            new_window = round_down_to_10_minutes(datetime.now()).isoformat()
            if new_window != vehicles["timeStamp"]:
                send_traffic(vehicles)
                vehicles = empty_vehicles(new_window)
                track_states = {}

            two_minutes_time = round_down_to_2_minutes(datetime.now())
            if two_minutes_time != current_two_minutes_window:
                current_two_minutes_window = two_minutes_time
                reader.stop()
                reader = create_reader()


        if frame_count % 500 == 0:
            track_states = {
                k: v for k, v in track_states.items() if k in active_ids
            }

finally:
    reader.stop()
    cv2.destroyAllWindows()
