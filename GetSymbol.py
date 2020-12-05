import datetime
import requests
import json
import re

if __name__ == "__main__":
    url = 'http://localhost:8080/Search'

    contract = {"symbol": "TLSA",
                "secType": "STK",
                "currency": "USD",
                "exchange": "SMART"
                }

    x = requests.post(url, data = contract)
    jsn = json.loads(x.text)
    skip = 0
    for j in jsn:
        if skip < 5:
            skip += 1
            continue
        j2 = json.loads(j)
        print("{}, {}, {}, {}, {}".format(
                j2["symbol"],
                j2["secType"],
                j2["currency"],
                j2["exchange"],
                j2["primaryExchange"]
            ))


