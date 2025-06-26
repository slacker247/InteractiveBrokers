import requests
from bs4 import BeautifulSoup
import time
import datetime
import threading

# Map background colors to status codes
STATUS_MAP = {
    '#cc3333': (0, 'Problem/Outage'),
    '#ffcc00': (1, 'Scheduled Maintenance'),
    '#99cccc': (2, 'General Info'),
    '#66cc33': (3, 'Normal Operations'),
    '#999999': (4, 'Resolved')
}

def parse_ib_system_status():
    url = 'https://www.interactivebrokers.com/en/software/systemStatus.php'
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for the colored status row
        rows = soup.select('tr.odd td.centeritem[style]')
        for color_cell in rows:
            style = color_cell.get('style')
            for color, (code, label) in STATUS_MAP.items():
                if color in style:
                    message_cell = color_cell.find_next_sibling('td')
                    message = message_cell.get_text(separator=' ', strip=True) if message_cell else ""
                    return {
                        'status_code': code,
                        'status_label': label,
                        'message': message,
                        'event_time': datetime.datetime.now()
                    }

        return {
            'status_code': -1,
            'status_label': 'Unknown',
            'message': 'Could not find a recognized status cell',
            'event_time': datetime.datetime.now()
        }

    except Exception as e:
        return {
            'status_code': -2,
            'status_label': 'Error',
            'message': str(e),
            'event_time': datetime.datetime.now()
        }
    
current_status = None
def status_check_th():
    global current_status
    while True:
        current_status = parse_ib_system_status()
        time.sleep(60*1)  # Health check every 1 minute


threading.Thread(target=status_check_th, daemon=True).start()

if __name__ == "__main__":
    a = "1"
    while a == "1":
        print(current_status)
        a = input("Enter 1 to continue:")










