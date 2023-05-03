let authKey = localStorage.getItem('authKey');

if (!authKey) {
    authKey = prompt('Please enter your auth key:');
    
    // Store the entered auth key in local storage
    if (authKey) {
      localStorage.setItem('authKey', authKey);
    }
}

const currentAlarm = document.getElementById("current-alarm");
const alarmTimeInput = document.getElementById("alarm-time");
const alarmEnabledInput = document.getElementById("alarm-enabled");
const tasksContainer = document.getElementById("tasks-container");

let alarmUpdateInterval;
let taskUpdateInterval;

function formatAlarmTime(time) {
    const [hour, minute] = time.split(':');
    const amOrPm = hour < 12 ? 'am' : 'pm';
    const formattedHour = hour % 12 || 12;
    return `${formattedHour}:${minute}${amOrPm}`;
}

function formatTimeUntil(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `in ${hours} hours ${minutes} minutes`;
}

let updateAlarmRequest = null;
function updateAlarm() {
    updateAlarmRequest = fetch("/api/v1/alarm",
        {headers: {
            'Authorization': `Bearer ${authKey}`,
            },
        })
        .then((response) => response.json())
        .then((data) => {
            const alarmTime = formatAlarmTime(data[0].time)
            const timeUntilAlarm = formatTimeUntil(data[1].time_until_alarm);
            currentAlarm.textContent = data[0].enabled
                ? `${alarmTime} (${timeUntilAlarm})`
                : "Disabled";
            alarmTimeInput.value = data[0].time;
            alarmEnabledInput.checked = data[0].enabled;
        });
}

let updateTaskRequest = null;
function updateTasks() {
    updateTaskRequest = fetch("/api/v1/task",
        {headers: {
            'Authorization': `Bearer ${authKey}`,
            },
        })
        .then((response) => response.json())
        .then((data) => {
            const taskButtons = document.querySelectorAll(".task-button");
            taskButtons.forEach((button) => {
                if (button.getAttribute("data-task") === data.task) {
                    button.classList.add("active");
                } else {
                    button.classList.remove("active");
                }
            });
        });
}

let setTaskRequest = null;
function initializeTasks() {
    fetch("/api/v1/tasks",
        {headers: {
            'Authorization': `Bearer ${authKey}`,
            },
        })
        .then((response) => response.json())
        .then((data) => {
            data.tasks.forEach((task) => {
                let taskElement;
                if (task === "static") {
                    taskElement = document.createElement("input");
                    taskElement.type = "color";
                    taskElement.className = "task-button";
                    taskElement.setAttribute("data-task", task);

                    function handleStaticColorChange(event) {
                        const rgb = event.target.value;
                        setTaskRequest = fetch("/api/v1/task", {
                            method: "POST",
                            headers: { "Content-Type": "application/json", 'Authorization': `Bearer ${authKey}` },
                            body: JSON.stringify({ task: "static", arg: [parseInt(rgb.slice(1, 3), 16), parseInt(rgb.slice(3, 5), 16), parseInt(rgb.slice(5, 7), 16)] }),
                        });
                        setTaskRequest.then(() => {
                            updateTasks();
                        });
                    }
                    taskElement.addEventListener("input", handleStaticColorChange);
                    taskElement.addEventListener("focus", handleStaticColorChange);
                } else {
                    taskElement = document.createElement("button");
                    taskElement.textContent = task;
                    taskElement.className = "task-button";
                    taskElement.setAttribute("data-task", task);
                    taskElement.addEventListener("click", () => {
                        // abort previous setTaskRequest if it exists and is still in flight
                        if (setTaskRequest && setTaskRequest.status === 0) {
                            setTaskRequest.abort();
                        }
                        setTaskRequest = fetch("/api/v1/task", {
                            method: "POST",
                            headers: { "Content-Type": "application/json", 'Authorization': `Bearer ${authKey}` },
                            body: JSON.stringify({ task: task }),
                        });
                        setTaskRequest.then(() => {
                            updateTasks();
                        });
                    });
                }
                tasksContainer.appendChild(taskElement);
            });
            updateTasks();
        });
}

function init() {
    updateAlarm();
    initializeTasks();
    alarmUpdateInterval = setInterval(updateAlarm, 60000);
    taskUpdateInterval = setInterval(updateTasks, 60000);
}

let setAlarmRequest = null;
alarmTimeInput.addEventListener("change", () => {
    clearInterval(alarmUpdateInterval);
    setAlarmRequest = fetch("/api/v1/alarm", {
        method: "POST",
        headers: { "Content-Type": "application/json", 'Authorization': `Bearer ${authKey}` },
        body: JSON.stringify({ time: alarmTimeInput.value, enabled: alarmEnabledInput.checked }),
    });
    setAlarmRequest.then(() => {
        updateAlarm();
        clearInterval(alarmUpdateInterval);
        alarmUpdateInterval = setInterval(updateAlarm, 60000);
    });
});

let setAlarmEnabledRequest = null;
alarmEnabledInput.addEventListener("change", () => {
    clearInterval(alarmUpdateInterval);
    setAlarmEnabledRequest = fetch("/api/v1/alarm", {
        method: "POST",
        headers: { "Content-Type": "application/json", 'Authorization': `Bearer ${authKey}` },
        body: JSON.stringify({ time: alarmTimeInput.value, enabled: alarmEnabledInput.checked }),
    });
    setAlarmEnabledRequest.then(() => {
        updateAlarm();
        clearInterval(alarmUpdateInterval);
        alarmUpdateInterval = setInterval(updateAlarm, 60000);
    });
});

init();
