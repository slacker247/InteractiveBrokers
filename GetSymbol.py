import datetime
import requests
import json
import re

if __name__ == "__main__":
    url = 'http://localhost:8080/Search'

    contract = {"term": "ES"
                }

    x = requests.post(url, data = contract)
    jsn = json.loads(x.text)
    skip = 0
    for j in jsn:
        if skip < 6:
            skip += 1
            continue
        print("{}".format(j))
        j2 = json.loads(j)
        print("{}, {}, {}, {}, {}".format(
                j2["symbol"],
                j2["secType"],
                j2["currency"],
                j2["exchange"],
                j2["primaryExchange"]
            ))


