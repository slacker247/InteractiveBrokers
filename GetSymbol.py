import datetime
import requests
import json
import re

def search(term:str):
    url = 'http://localhost:8080/Search'

    contract = {"term": term}

    x = requests.post(url, data = contract)
    jsn = {}
    try:
        jsn = json.loads(x.text)
    except:
        print("1 Error: {}".format(x.text))

    for j in jsn:
        try:
            j2 = json.loads(j)
            print("{}, {}, {}, {}, {}".format(
                    j2["symbol"],
                    j2["secType"],
                    j2["currency"],
                    j2["exchange"],
                    j2["primaryExchange"]
                ))
        except:
            print("1 parse error: {}".format(j))
    return

def contractLookup(symbol, secType, exchange):
    url = 'http://localhost:8080/ContractDetails'

    print("-------   Contract details --------")
    contract = {"symbol": symbol,
                "secType": secType,
                "exchange": exchange
                }

    x = requests.post(url, data = contract)

    jsn = {}
    try:
        jsn = json.loads(x.text)
    except:
        print("2 Error: {}".format(x.text))

    skip = 0
    for j in jsn:
        try:
            j2 = json.loads(j)
            print("{}, {}, {}, {}, {}, {}, {}".format(
                    j2["symbol"],
                    j2["localSymbol"],
                    j2["secType"],
                    j2["currency"],
                    j2["exchange"],
                    j2["primaryExchange"],
                    j2["lastTradeDateOrContractMonth"]
                ))
            #print(j2)
        except:
            print("2 parse error: {}".format(j))
            #print("jsn: {}".format(jsn))
    return

if __name__ == "__main__":
    #search("futures")
    contractLookup("ES", "FUT", "GLOBEX")
    #contractLookup("AMZN", "STK", "ISLAND") # island is nasdaq...

