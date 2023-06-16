import datetime
import requests
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

def search(term:str):
    url = host + '/Search'

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
    url = host + '/ContractDetails'

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
    return

if __name__ == "__main__":
    #search("LZB")
    contractLookup("TLSA", "STK", "ISLAND")
    #contractLookup("AMZN", "STK", "") # island is nasdaq...

