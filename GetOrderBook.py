import datetime
import requests
import socket
import json
import re

def extract_ip():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:       
        st.connect(('10.255.255.255', 1))
        IP = st.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        st.close()
    return IP

host = 'http://' + extract_ip() + ':8080'

if __name__ == "__main__":
    url = host + '/OrderBook'

    contract = {"symbol": "ES",
                "secType": "FUT",
                "currency": "USD",
                "exchange": "GLOBEX", # this is nasdaq...
                "localSymbol": "ESH1",
                "depth" : "5"
                }

    #  ([0-9]+):( \w+: ([\-\.0-9]+),)+
    x = requests.post(url, data = contract)
    if "error" in x.text:
        print("{}".format(x.text))
    # side: 0 for ask, 1 for bid
    jsn = json.loads(x.text)
    for j in jsn:
        print("{}".format(j))


