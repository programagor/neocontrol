import importlib
from flask import Flask, request, jsonify, render_template
import threading
import schedule
import datetime
import json
import os
import sys

# Check if rpi_ws281x library is available
rpi_ws281x_spec = importlib.util.find_spec("rpi_ws281x")
if rpi_ws281x_spec is not None:
    import rpi_ws281x as ws
else:
    # Define dummy class for local testing
    class DummyPixelStrip:
        def __init__(self, *args, **kwargs):
            self.num_pixels = kwargs.get('led_count', 4)

        def begin(self):
            print("Dummy strip: begin")

        def setPixelColor(self, i, color_obj):
            print(f"Dummy strip: set pixel color at index {i} to {color_obj}")

        def show(self):
            print("Dummy strip: show")

        def numPixels(self):
            return self.num_pixels

    def DummyColor(*color):
        return color

    # Replace rpi_ws281x with dummy implementation
    ws = type("Dummy_rpi_ws281x", (object,), {
        "PixelStrip": DummyPixelStrip,
        "Color": DummyColor,
        "WS2811_STRIP_GRB": "Dummy_WS2811_STRIP_GRB"
    })


app = Flask(__name__, static_folder='static', static_url_path='')

ALARM_FILE = "alarm.json"

# Load alarm data from the file, or set the default alarm
if os.path.exists(ALARM_FILE):
    with open(ALARM_FILE, 'r') as f:
        alarm_data = json.load(f)
else:
    alarm_data = {"time": "06:30", "enabled": True}
    with open(ALARM_FILE, 'w') as f:
        json.dump(alarm_data, f)

worker_thread = None
current_task = None
task_lock = threading.Lock() # so only one worker at a time modifies which task is running
alarm_lock = threading.Lock() # so only one worker at a time modifies alarm data
exit_event = threading.Event() # to quit worker thread
alarm_update_event = threading.Event() # to update alarm time or enabled status

LED_COUNT = 120
GPIO_PIN = 10
STRIP_TYPE = ws.WS2811_STRIP_GRB
BRIGHTNESS = 230
TARGET_FREQ = 1200000
DMA = 10

strip = ws.PixelStrip(LED_COUNT, GPIO_PIN, TARGET_FREQ, DMA, invert=False, brightness=BRIGHTNESS, strip_type=STRIP_TYPE)
strip.begin()

TASKS = {}
for task_file in os.listdir('tasks'):
    if task_file.endswith('.py') and task_file not in ['__init__.py', 'common.py']:
        task_name = task_file[:-3]
        module = importlib.import_module(f'tasks.{task_name}')
        TASKS[task_name] = getattr(module, task_name)

def stop_worker_thread():
    global worker_thread, exit_event
    if worker_thread and worker_thread.is_alive():
        exit_event.set()
        worker_thread.join()
        exit_event.clear()

def alarm_triggered():
    global worker_thread, current_task, alarm_data, alarm_lock, task_lock, exit_event, strip
    print("alarm_triggered")
    enabled = False
    with alarm_lock:
        enabled = alarm_data["enabled"]
    if enabled:
        print("alarm_triggered: enabled")
        with task_lock:
            print("alarm_triggered: stopping worker thread")
            stop_worker_thread()
            current_task = "sunrise"
            worker_thread = threading.Thread(target=TASKS[current_task], args=(strip, exit_event), daemon=True)
            print("alarm_triggered: starting worker thread")
            worker_thread.start()
            print("alarm_triggered: worker thread started")

alarm_scheduler = schedule.every().day.at(alarm_data["time"]).do(alarm_triggered)

def check_alarm():
    global alarm_scheduler, alarm_update_event
    while True:
        print("check_alarm will run all pending jobs")
        schedule.run_pending()
        print("check_alarm ran all pending jobs")
        next_run = schedule.idle_seconds()
        print(f"check_alarm will run again in {next_run} seconds")
        alarm_update_event.wait(next_run)
        print("check_alarm was woken up by alarm_update_event or timeout")
        alarm_update_event.clear()



alarm_thread = threading.Thread(target=check_alarm, daemon=True)
alarm_thread.start()


@app.route('/api/v1/alarm', methods=['POST'])
def set_alarm():
    global alarm_data, alarm_scheduler
    data = request.get_json()
    
    with alarm_lock:
        if "time" in data:
            # make sure alarm_data["time"] is in the format HH:MM (including leading zeros)
            try:
                alarm_data["time"] = datetime.datetime.strptime(data["time"], "%H:%M").strftime("%H:%M")
                schedule.cancel_job(alarm_scheduler)
                alarm_scheduler = schedule.every().day.at(alarm_data["time"]).do(alarm_triggered)
                alarm_update_event.set()
            except:
                return jsonify({"error": "Invalid time format"}), 400

        if "enabled" in data:
            alarm_data["enabled"] = data["enabled"]

    with open(ALARM_FILE, 'w') as f:
        json.dump(alarm_data, f)

    return jsonify((alarm_data, {"time_until_alarm": schedule.idle_seconds()}))


@app.route('/api/v1/alarm', methods=['GET'])
def get_alarm():
    with alarm_lock:
        return jsonify((alarm_data, {"time_until_alarm": schedule.idle_seconds()}))


@app.route('/api/v1/task', methods=['POST'])
def set_task():
    global worker_thread, current_task
    task = request.get_json().get("task")
    #if arg was provided, pass it to the task
    arg = request.get_json().get("arg") or None

    if task not in TASKS:
        return jsonify({"error": "Invalid task"}), 400

    with task_lock:
        stop_worker_thread()
        current_task = task
        worker_thread = threading.Thread(target=TASKS[task], args=(strip, exit_event, arg), daemon=True)
        worker_thread.start()

    return jsonify({"task": current_task})


@app.route('/api/v1/task', methods=['GET'])
def get_task():
    global current_task
    with task_lock:
        return jsonify({"task": current_task})

@app.route('/api/v1/tasks', methods=['GET'])
def get_tasks():
    return jsonify({"tasks": list(TASKS.keys())})

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
