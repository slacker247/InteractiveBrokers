import subprocess
import datetime
import time
import psutil
import pygetwindow as gw
from pywinauto.application import Application
from pywinauto.keyboard import send_keys

# DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP flags
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

def stop_process(proc):
    proc.terminate()
    try:
        proc.wait(timeout=3)
        print(f"Terminated: {proc.info}")
    except psutil.TimeoutExpired:
        print(f"Timeout - killing: {proc.info}")
        proc.kill()

def find_process(target_name):
    procs = []
    # Find a process by name
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == target_name:
            procs.append(proc)
    return procs

def read_name_value_file(filename):
    data = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or '=' not in line:
                continue  # Skip empty or malformed lines
            key, value = line.split('=', 1)
            data[key.strip()] = value.strip()
    return data

def launch_tws():
    # Step 1: Launch the program
    subprocess.Popen(
        args="C:\\IBKR\\tws.exe -J-DjtsConfigDir=\"C:\\IBKR\"",
        cwd="C:\\IBKR"
    )

    # Step 2: Wait for the window to appear
    time.sleep(15)  # Adjust based on app launch time

    # Step 3: Find the window by title
    win = None
    for w in gw.getWindowsWithTitle("Login"):
        win = w
        break

    if not win:
        raise RuntimeError("Interactive Brokers window not found")

    # Step 4: Connect to the window using pywinauto
    app = Application(backend="uia").connect(title_re="Login")
    app_window = app.window(title_re="Login")

    # Step 5: Bring the window to front
    app_window.set_focus()

    settings = read_name_value_file("secrets.ini")
    # Step 6: Send keys
    send_keys(settings["username"], with_spaces=True)
    time.sleep(1)
    send_keys('{TAB}')
    time.sleep(1)
    send_keys(settings["password"], with_spaces=True)
    time.sleep(1)
    send_keys('{ENTER}')

if __name__ == "__main__":
    last_seen = datetime.datetime(1970, 1, 1)

    while True:
        dt = datetime.datetime.now()
        print(f"{dt} - check for tws.exe...")
        procs = find_process("tws.exe")
        if len(procs) > 0:
            last_seen = datetime.datetime.now()
        else:
            dt = datetime.datetime.now()
            print(f"{dt} - check for python.exe server.py...")
            p2 = find_process("python.exe")
            p1 = None
            for p in p2:
                if "server.py" in p.info["cmdline"]:
                    p1 = p
            if p1 != None:
                dt = datetime.datetime.now()
                print(f"{dt} - stopping server.py...")
                stop_process(p1)
            pass
        delta = datetime.datetime.now() - last_seen
        if delta > datetime.timedelta(minutes=30):
            dt = datetime.datetime.now()
            print(f"{dt} - starting tws.exe...")
            launch_tws()

            print(f"{dt} - starting server.py...")
            #subprocess.Popen(
            #    'start "server.py" python -u server.py',
            #    cwd="C:\\projects\\InteractiveBrokers\\",
            #    shell=True
            #)

        time.sleep(60)

