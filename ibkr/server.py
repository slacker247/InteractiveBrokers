import os.path
import sys

db_import = os.path.join(sys.path[0], "C:\\TWS API\\source\\pythonclient")
print(db_import)
sys.path.insert(1, db_import)

from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import datetime
import urllib.parse
import hashlib

from ibapi.common import * # @UnusedWildImport
from ibapi.contract import * # @UnusedWildImport
from TestApp import TestApp

hostName = "localhost"
serverPort = 8080

class Server(BaseHTTPRequestHandler):
    IBKApp = None
    Cache = {}

    def waitForResponse(self, reqId):
        found = False
        timeout = False
        start = datetime.datetime.now()
        while(not found and not timeout):
            time.sleep(0.12)
            if not self.IBKApp.Msg[reqId] == "running":
                found = True
            if datetime.datetime.now() - start > datetime.timedelta(minutes=2):
                timeout = True
        return found

    def do_POST(self):
        self.send_response(501) # Not Implemented           
        jsn = "{error:'Failed to execute request'}"
        length = int(self.headers['content-length'])
        field_data = self.rfile.read(length)
        fields = urllib.parse.parse_qs(str(field_data).replace("b'", "")
                .replace("['", "")
                .replace("']", "")
                .replace('"', "")
                .replace("'", ""))
        print("fields: {}".format(fields))
        if self.path == "/Ticks":
            # parse params
            contract = Contract()
            # this should be in the contract class
            if "symbol" in fields:
                contract.symbol = str(fields["symbol"][0])
            if "secType" in fields:
                contract.secType = str(fields["secType"][0])
            if "lastTradeDateOrContractMonth" in fields:
                contract.lastTradeDateOrContractMonth = str(fields["lastTradeDateOrContractMonth"][0])
            if "strike" in fields:
                contract.strike = float(fields["strike"][0])
            if "right" in fields:
                contract.right = str(fields["right"][0])
            if "multiplier" in fields:
                contract.multiplier = str(fields["multiplier"][0])
            if "exchange" in fields:
                contract.exchange = str(fields["exchange"][0])
            if "primaryExchange" in fields:
                contract.primaryExchange = str(fields["primaryExchange"][0])
            if "currency" in fields:
                contract.currency = str(fields["currency"][0])
            if "localSymbol" in fields:
                contract.localSymbol = str(fields["localSymbol"][0])
            if "tradingClass" in fields:
                contract.tradingClass = str(fields["tradingClass"][0])
            if "includeExpired" in fields:
                contract.includeExpired = bool(fields["includeExpired"][0])
            if "secIdType" in fields:
                contract.secIdType = str(fields["secIdType"][0])
            if "secId" in fields:
                contract.secId = str(fields["secId"][0])

            endDateTime = (datetime.datetime.today() - datetime.timedelta(days=180)).strftime("%Y%m%d %H:%M:%S")
            if "endDateTime" in fields:
                endDateTime = str(fields["endDateTime"][0])
            durationStr = "1 M"
            if "durationStr" in fields:
                durationStr = str(fields["durationStr"][0])
            barSizeSetting = "1 day"
            if "barSizeSetting" in fields:
                barSizeSetting = str(fields["barSizeSetting"][0])
            whatToShow = "MIDPOINT"
            if "whatToShow" in fields:
                whatToShow = str(fields["whatToShow"][0])
            useRTH = 1
            if "useRTH" in fields:
                useRTH = int(fields["useRTH"][0])
            formatDate = 1
            if "formatDate" in fields:
                formatDate = int(fields["formatDate"][0])
            
            print("constract: {}".format(contract))
            reqId = 4102
            # queryTime the period for which to get ticks
            self.IBKApp.Msg[reqId] = "running"
            self.IBKApp.reqHistoricalData(reqId, contract, endDateTime,
                               durationStr, barSizeSetting, whatToShow,
                               useRTH, formatDate, False, [])
            results = []
            timeout = self.waitForResponse(reqId)
            
            if self.IBKApp.Msg[reqId] == "success":
                tempQueue = self.IBKApp.Queue.copy()
                for q in tempQueue:
                    if isinstance(q, BarData):
                        results.append(q)
                    elif isinstance(q, HistogramDataList):
                        for hd in q:
                            results.append(hd)
                    else:
                        results.append(q)
                    self.IBKApp.Queue.remove(q)
                jsn = "{}".format(results)
            elif self.IBKApp.Msg[reqId] == "error":
                jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
            self.send_response(200)            
            pass
        if self.path == "/Search":
            print("Calling Search...")
            contract = Contract()
            contract.symbol = "FISV"
            contract.secType = "OPT"
            contract.currency = "USD"
            contract.exchange = "SMART"
            if "symbol" in fields:
                contract.symbol = str(fields["symbol"][0])
            if "secType" in fields:
                contract.secType = str(fields["secType"][0])
            if "currency" in fields:
                contract.currency = str(fields["currency"][0])
            if "exchange" in fields:
                contract.exchange = str(fields["exchange"][0])
            
            hsh = "{}".format(contract.__dict__) + "{}".format(datetime.date.today())

            if hsh in self.Cache:
                print("Using cache: {}".format(hsh))
                jsn = self.Cache[hsh]
            else:
                reqId = 210
                self.IBKApp.Msg[reqId] = "running"
                self.IBKApp.reqContractDetails(reqId, contract)

                timeout = self.waitForResponse(reqId)

                results = []
                if self.IBKApp.Msg[reqId] == "success":
                    # might need to change the Queue to index the request id
                    tempQueue = self.IBKApp.Queue.copy()
                    for q in tempQueue:
                        if isinstance(q, ContractDetails):
                            conDets = q.__dict__
                            if "contract" in conDets:
                                con = conDets["contract"].__dict__
                                del conDets["contract"]
                                secIdList = conDets["secIdList"]
                                del conDets["secIdList"]
                                con["details"] = conDets
                                con["secIdList"] = "{}".format(secIdList)

                                try:
                                    results.append(json.dumps(con))
                                except Exception as ex:
                                    print("{}".format(ex))
                                    print(con)
                            else:
                                results.append(json.dumps(conDets))
                        else:
                            results.append(q)
                            
                        self.IBKApp.Queue.remove(q)
                    jsn = json.dumps(results)
                    self.Cache[hsh] = jsn
                elif self.IBKApp.Msg[reqId] == "error":
                    jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
            
            self.send_response(200)
            pass
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(jsn, "utf-8"))
        pass


    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")