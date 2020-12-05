import datetime
import requests
import json
import re

if __name__ == "__main__":
    url = 'http://localhost:8080/Ticks'

    contract = {"symbol": "TLSA",
                "secType": "STK",
                "currency": "USD",
                "exchange": "SMART",
                "durationStr" : "25 D",
                "endDateTime" : datetime.datetime.today().strftime("%Y%m%d %H:%M:%S")
                }

    #  ([0-9]+):( \w+: ([\-\.0-9]+),)+
    pattern = "([0-9]+): Date: ([0-9]+), Open: ([\\-0-9\\.]+), High: ([\\-0-9\\.]+), Low: ([\\-0-9\\.]+), Close: ([\\-0-9\\.]+), Volume: ([\\-0-9\\.]+), Average: ([\\-0-9\\.]+), BarCount: ([\\-0-9\\.]+)"
    x = requests.post(url, data = contract)
    print("{}".format(x.text))
    mt = re.findall(pattern, x.text)
    #print("{}".format(mt))
    found = False
    for m in mt:
        found = True
        print("Date: {}, Open: {}, High: {}, Low: {}, Close: {}, Volume: {}, Average: {}, BarCount: {}"
            .format(m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8]))

    if not found:
        print(x.text)

