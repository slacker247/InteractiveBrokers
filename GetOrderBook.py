import datetime
import requests
import json
import re

if __name__ == "__main__":
    url = 'http://localhost:8080/OrderBook'

    contract = {"symbol": "ES",
                "secType": "FUT",
                "currency": "USD",
                "exchange": "GLOBEX", # this is nasdaq...
                "localSymbol": "ESH1",
                "depth" : "5"
                }

    #  ([0-9]+):( \w+: ([\-\.0-9]+),)+
    x = requests.post(url, data = contract)
    #print("{}".format(x.text))
    # side: 0 for ask, 1 for bid
    jsn = json.loads(x.text)
    for j in jsn:
        print("{}".format(j))

