import subprocess
import time
import psutil
import win32gui
import win32process
import pygetwindow as gw
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import os
import sys

TWS_PATH = "C:\\IBKR\\tws.exe"
TWS_WORKDIR = "C:\\IBKR"
SECRETS_FILE = "secrets.ini"
SERVER_SCRIPT = "C:\\projects\\InteractiveBrokers\\handler.py"

LOGIN_TITLE = "Login"
MAIN_WINDOW_KEYWORD = "Interactive Brokers"
RECONNECT_DIALOG_KEYWORD = "Trying to reconnect"


def stop_process(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
        print(f"[INFO] Terminated: {proc.info}")
    except psutil.TimeoutExpired:
        print(f"[WARN] Timeout - killing: {proc.info}")
        proc.kill()

def find_process(name, cmd_contains=None):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == name:
            if cmd_contains:
                if any(cmd_contains in str(arg) for arg in proc.info['cmdline']):
                    return proc
            else:
                return proc
    return None

def enum_windows_for_exe(exe_name):
    # Get all PIDs for the given executable
    matching_pids = [p.pid for p in psutil.process_iter(['name']) if p.info['name'] == exe_name]

    windows = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid in matching_pids:
                    title = win32gui.GetWindowText(hwnd)
                    windows.append((hwnd, title))
            except:
                pass

    win32gui.EnumWindows(callback, None)
    return windows

def read_settings_file(filename):
    data = {}
    with open(filename, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                data[key.strip()] = value.strip()
    return data

def launch_server():
    if not os.path.exists(SERVER_SCRIPT):
        print(f"[ERROR] handler.py not found at {SERVER_SCRIPT}")
        return

    proc = find_process("python.exe", cmd_contains="handler.py")
    if proc:
        print("[INFO] handler.py already running. No action taken.")
        return

    print("[INFO] Launching handler.py...")
    subprocess.Popen(
        'start "handler.py" python -u handler.py',
        cwd="C:\\projects\\InteractiveBrokers\\",
        shell=True
    )

def stop_server():
    proc = find_process("python.exe", cmd_contains="handler.py")
    if proc:
        print(f"[INFO] Stopping handler.py with PID {proc.pid}...")
        stop_process(proc)
    else:
        print("[INFO] handler.py not running.")

def monitor_tws():
    state = "UNK"
    proc = find_process("tws.exe")
    if proc == None:
        state = "Not Running"
    else:
        windows = enum_windows_for_exe("tws.exe")
        for hwnd, title in windows:
            if title == "Login":
                state = "Login"
            if MAIN_WINDOW_KEYWORD in title:
                state = "Running"
            #print(f"[DEBUG] window title: {title}")

    if state == "Not Running":
        print("[INFO] Launching TWS...")
        subprocess.Popen(
            args=[TWS_PATH, '-J-DjtsConfigDir=C:\\IBKR'],
            cwd=TWS_WORKDIR,
        )
    if state == "Login":
        try:
            app = Application(backend="uia").connect(title_re=LOGIN_TITLE)
            app_window = app.window(title_re=LOGIN_TITLE)
            app_window.set_focus()
            creds = read_settings_file(SECRETS_FILE)
            send_keys(creds["username"], with_spaces=True)
            time.sleep(1)
            send_keys('{TAB}')
            time.sleep(1)
            send_keys(creds["password"], with_spaces=True)
            time.sleep(1)
            send_keys('{ENTER}')
            print("[INFO] Login submitted.")
            time.sleep(60)
        except Exception as e:
            print(f"[ERROR] Login automation failed: {e}")

    if state == "Running":
        launch_server()
        pass
    else:
        print("[WARN] Stopping handler.py...")
        stop_server()

if __name__ == "__main__":
    stop_server()
    while True:
        monitor_tws()
        time.sleep(60)



