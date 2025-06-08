import importlib
from flask import Flask, request, jsonify, render_template
import threading
import schedule
import datetime
import json
import os
import sys
from tasks.common import ws

# Create instance of the Flask app
app = Flask(__name__, static_folder='static', static_url_path='')


# Load alarm data from the file, or set the default alarm
ALARM_FILE = "alarm.json"
TIMEZONE = os.environ.get("TIMEZONE", os.environ.get("TZ", "UTC"))
DEFAULT_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
if os.path.exists(ALARM_FILE):
    with open(ALARM_FILE, 'r') as f:
        alarm_data = json.load(f)
    if "days" not in alarm_data:
        alarm_data["days"] = DEFAULT_DAYS
else:
    alarm_data = {"time": "06:30", "enabled": True, "days": DEFAULT_DAYS}
    with open(ALARM_FILE, 'w') as f:
        json.dump(alarm_data, f)

worker_thread : threading.Thread = None                    # This thread controls the LEDs
current_task : str = None                     # Name of the currently running task
task_lock = threading.Lock()            # so only one worker at a time modifies which task is running
alarm_lock = threading.Lock()           # so only one worker at a time modifies alarm data
exit_event = threading.Event()          # to quit worker thread
alarm_update_event = threading.Event()  # to update alarm time or enabled status

LED_COUNT = 120 * 3
GPIO_PIN = 10 # Pin to which the LED strip is connected
STRIP_TYPE = ws.WS2811_STRIP_GRB
BRIGHTNESS = 255 # 0-255
TARGET_FREQ = 1200000 # Found empirically
DMA = GPIO_PIN # Because the DMA channel is connected to the GPIO pin

# Create NeoPixel object with appropriate configuration
strip = ws.PixelStrip(LED_COUNT, GPIO_PIN, TARGET_FREQ, DMA, invert=False, brightness=BRIGHTNESS, strip_type=STRIP_TYPE)
# Intialize the library (must be called once before other functions)
strip.begin()

# Load available tasks from the tasks directory
TASKS = {}
for task_file in os.listdir('tasks'):
    if task_file.endswith('.py') and task_file not in ['__init__.py', 'common.py']:
        # Get the name of the task from the filename
        task_name = task_file.split('.')[0]
        # Import the module
        module = importlib.import_module(f'tasks.{task_name}')
        # Add the task to the dictionary
        TASKS[task_name] = getattr(module, task_name)

# Function to stop the worker thread
def stop_worker_thread():
    global worker_thread, exit_event
    print(f"[{datetime.datetime.now()}] stop_worker_thread() thread: {threading.get_ident()} {threading.current_thread().name}")
    if worker_thread and worker_thread.is_alive():
        print(f"[{datetime.datetime.now()}] stop_worker_thread: setting exit event")
        # Sent the exit event to the worker thread
        exit_event.set()
        # Wait for the worker thread to finish
        # All tasks should periodically check for the exit event and exit gracefully
        # Python doesn't have a way to kill threads, so this is the best we can do
        print(f"[{datetime.datetime.now()}] stop_worker_thread: joining worker thread")
        worker_thread.join()
        # The worker thread should have exited by now
        print(f"[{datetime.datetime.now()}] stop_worker_thread: worker thread joined")
        # Unset the exit event, so a new worker thread can be started again
        exit_event.clear()
    print(f"[{datetime.datetime.now()}] stop_worker_thread: done")

# Function which is called when the alarm is triggered
def alarm_triggered():
    global worker_thread, current_task, alarm_data, alarm_lock, task_lock, exit_event, strip
    print(f"[{datetime.datetime.now()}] alarm_triggered() thread: {threading.get_ident()} {threading.current_thread().name}")
    enabled = False
    # Check if the alarm is enabled
    with alarm_lock:
        enabled = alarm_data["enabled"]
        print(f"[{datetime.datetime.now()}] alarm_triggered: alarm enabled: {enabled}")
    # If the alarm is not enabled, there is nothing to do. Otherwise:
    if enabled:
        print(f"[{datetime.datetime.now()}] alarm_triggered: enabled")
        with task_lock:
            print(f"[{datetime.datetime.now()}] alarm_triggered: stopping worker thread")
            stop_worker_thread()
            print(f"[{datetime.datetime.now()}] alarm_triggered: preparing new worker thread")
            current_task = "sunrise" # TODO: make this configurable
            worker_thread = threading.Thread(target=TASKS[current_task], args=(strip, exit_event), daemon=True)
            print(f"[{datetime.datetime.now()}] alarm_triggered: starting new worker thread")
            worker_thread.start()
            print(f"[{datetime.datetime.now()}] alarm_triggered: worker thread started")
    print(f"[{datetime.datetime.now()}] alarm_triggered: done")

# Initialize the alarm scheduler
alarm_schedulers = []

def schedule_alarm():
    global alarm_schedulers
    for job in alarm_schedulers:
        schedule.cancel_job(job)
    alarm_schedulers = []
    for day in alarm_data["days"]:
        job = getattr(schedule.every(), day).at(alarm_data["time"], tz=TIMEZONE).do(alarm_triggered)
        alarm_schedulers.append(job)

schedule_alarm()

# Function which triggers the alarm on schedule
def check_alarm():
    global alarm_schedulers, alarm_update_event
    print(f"[{datetime.datetime.now()}] check_alarm() thread: {threading.get_ident()} {threading.current_thread().name}")
    # Never stop checking the alarm
    while True:
        print(f"[{datetime.datetime.now()}] check_alarm: schedule queue: {schedule.jobs}")
        print(f"[{datetime.datetime.now()}] check_alarm will run all pending jobs")
        schedule.run_pending()
        print(f"[{datetime.datetime.now()}] check_alarm ran all pending jobs")
        print(f"[{datetime.datetime.now()}] check_alarm: schedule queue: {schedule.jobs}")
        # Check how long until the next alarm
        next_run = schedule.idle_seconds()
        print(f"[{datetime.datetime.now()}] check_alarm will run again in {next_run} seconds")
        # Wait until the next alarm or until the alarm is updated
        alarm_update_event.wait(next_run)
        if alarm_update_event.is_set():
            print(f"[{datetime.datetime.now()}] check_alarm was woken up by alarm_update_event")
            # Unset the event which woke up the thread, so it can be used again
            alarm_update_event.clear()
        else:
            print(f"[{datetime.datetime.now()}] check_alarm was woken up by schedule")
        print(f"[{datetime.datetime.now()}] check_alarm will run again")
    # This should never be reached, because the loop is infinite and there is no break
    # The check_alarm thread is daemonised, so it will stop only when the main thread stops
    print(f"[{datetime.datetime.now()}] check_alarm: done")

# Start the check_alarm thread
# This thread will run forever, so it is daemonised
# It will be stopped when the main thread stops
# The check_alarm thread will check the alarm schedule and trigger the alarm when needed
print(f"[{datetime.datetime.now()}] starting check_alarm thread")
alarm_thread = threading.Thread(target=check_alarm, daemon=True)
alarm_thread.start()
print(f"[{datetime.datetime.now()}] check_alarm thread started")

with task_lock:
    stop_worker_thread()
    current_task = "fairy_lights"
    worker_thread = threading.Thread(target=TASKS[current_task], args=(strip, exit_event), daemon=True)
    worker_thread.start()

# Setting the alarm
@app.route('/api/v1/alarm', methods=['POST'])
def set_alarm():
    global alarm_data, alarm_schedulers
    data = request.get_json()
    
    print(f"[{datetime.datetime.now()}] set_alarm() thread: {threading.get_ident()} {threading.current_thread().name}")
    print(f"[{datetime.datetime.now()}] set_alarm: entering alarm_lock")
    # We will be modifying the alarm_data dictionary, so we need to lock it
    with alarm_lock:
        print(f"[{datetime.datetime.now()}] set_alarm: entered alarm_lock")
        # If the request contains the "time" key, we will update the alarm time
        changed = False
        if "time" in data:
            # The supplied time must be in the format HH:MM
            try:
                print(f"[{datetime.datetime.now()}] set_alarm: setting alarm time to {data['time']}")
                # Convert the time to HH:MM
                alarm_data["time"] = datetime.datetime.strptime(data["time"], "%H:%M").strftime("%H:%M")
                changed = True
            except:
                return jsonify({"error": "Invalid time format"}), 400
        if "days" in data:
            days = [d.lower() for d in data["days"]]
            alarm_data["days"] = days
            changed = True
        # If the request contains the "enabled" key, we will update the alarm enabled state
        if "enabled" in data:
            alarm_data["enabled"] = data["enabled"]
        if changed:
            schedule_alarm()
            print(f"[{datetime.datetime.now()}] set_alarm: setting alarm_update_event")
            alarm_update_event.set()
    print(f"[{datetime.datetime.now()}] set_alarm: exiting alarm_lock")

    # Save the updated alarm data to the file
    with open(ALARM_FILE, 'w') as f:
        json.dump(alarm_data, f)

    # Respond with the new alarm details, and the delay until the next alarm
    return jsonify((alarm_data, {"time_until_alarm": schedule.idle_seconds()}))

# Reading the alarm
@app.route('/api/v1/alarm', methods=['GET'])
def get_alarm():
    # We will be reading the alarm_data dictionary, so we need to lock it
    with alarm_lock:
        # Respond with the current alarm details, and the delay until the next alarm
        return jsonify((alarm_data, {"time_until_alarm": schedule.idle_seconds()}))

# Setting the task
@app.route('/api/v1/task', methods=['POST'])
def set_task():
    global worker_thread, current_task
    task = request.get_json().get("task")
    #if argument was provided (e.g. colour), pass it to the task. Otherwise, pass None
    arg = request.get_json().get("arg") or None

    if task not in TASKS:
        # The requested task is not available
        return jsonify({"error": "Invalid task"}), 400

    # We will be modifying the worker_thread and current_task variables, so we need to lock them
    with task_lock:
        print(f"[{datetime.datetime.now()}] set_task: stopping worker thread")
        stop_worker_thread()
        print(f"[{datetime.datetime.now()}] set_task: stopped worker thread")
        # Set the current task to the requested task
        current_task = task
        # Create a new worker thread with the requested task
        worker_thread = threading.Thread(target=TASKS[task], args=(strip, exit_event, arg), daemon=True)
        print(f"[{datetime.datetime.now()}] set_task: starting worker thread with task {task}")
        worker_thread.start()
        print(f"[{datetime.datetime.now()}] set_task: worker thread started")
    # Respond with the new task
    return jsonify({"task": current_task})

# Reading the currently running task
@app.route('/api/v1/task', methods=['GET'])
def get_task():
    global current_task
    # We will be reading the current_task variable, so we need to lock it
    with task_lock:
        return jsonify({"task": current_task})

# Getting all available tasks
@app.route('/api/v1/tasks', methods=['GET'])
def get_tasks():
    # Order TASKS.keys() alphabetically and return it as a list
    tasks = list(TASKS.keys())
    tasks.sort()
    return jsonify({"tasks": tasks})

# Frontend
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Start the dev web server if this script is run directly
if __name__ == '__main__':
    print(f"[{datetime.datetime.now()}] main thread: {threading.get_ident()} {threading.current_thread().name}")
    app.run(host="0.0.0.0", port=5000)
    print(f"[{datetime.datetime.now()}] main thread: done")