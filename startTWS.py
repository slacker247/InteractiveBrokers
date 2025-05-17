import subprocess
import time
import pygetwindow as gw
from pywinauto.application import Application
from pywinauto.keyboard import send_keys

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

