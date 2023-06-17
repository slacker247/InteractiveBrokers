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
from ibapi.account_summary_tags import AccountSummaryTags
from TestApp import TestApp

hostName = "localhost"
serverPort = 8080

class Server(BaseHTTPRequestHandler):
    IBKApp = None
    Cache = {}

    def parseContractParm(self, fields):
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
        return contract

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
        return timeout

    # this is called when the server starts up.
    def getNextOrderId(self):
        reqId = -5001
        self.IBKApp.Msg[reqId] = "running"
        self.IBKApp.reqIds(reqId)
        timeout = self.waitForResponse(reqId)
        nextId = self.IBKApp.nextOrderId()
        return nextId

    def placeLimitOrder(self, contract, price, qty, action):
        nextId = self.IBKApp.nextOrderId()
        reqId = -5002
        self.IBKApp.Msg[reqId] = "running"

        order = {
            "action": action,
            "orderType": "LMT",
            "totalQuantity": qty,
            "lmtPrice": price
        }

        if nextId >= 0:
            self.IBKApp.placeOrder(nextId, contract, order)

            results = []
            timeout = self.waitForResponse(reqId)
            
            if self.IBKApp.Msg[reqId] == "success":
                results.append(self.Queue.pop())
                jsn = json.dumps(results)
            elif self.IBKApp.Msg[reqId] == "error":
                jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
            self.send_response(200)
        return jsn

    def getOpenOrders(self):
        reqId = -5002
        self.IBKApp.Msg[reqId] = "running"

        self.reqOpenOrders()

        results = []
        timeout = self.waitForResponse(reqId)
        
        if self.IBKApp.Msg[reqId] == "success":
            results.append(self.Queue.pop())
            jsn = json.dumps(results)
        elif self.IBKApp.Msg[reqId] == "error":
            jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
        self.send_response(200)
        return jsn

    def getClosedOrders(self):
        reqId = -5002
        self.IBKApp.Msg[reqId] = "running"

        self.reqCompletedOrders(False)

        results = []
        timeout = self.waitForResponse(reqId)
        
        if self.IBKApp.Msg[reqId] == "success":
            results.append(self.Queue.pop())
            jsn = json.dumps(results)
        elif self.IBKApp.Msg[reqId] == "error":
            jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
        self.send_response(200)
        return jsn

    def getOrders(self):

        pass

    def getOrderStatus(self, id):

        jsn = json.dumps({"status":"error", "msg":"Order Status - Not Implemented"})
        return jsn

    def cancelOrder(self, id):
        reqId = -5003
        self.IBKApp.Msg[reqId] = "running"
        self.IBKApp.cancelOrder(id)
        results = []
        sleep(0.12)
        if self.IBKApp.Msg[reqId] == "success":
            jsn = self.getOrderStatus(id)
        elif self.IBKApp.Msg[reqId] == "error":
            jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
        self.send_response(200)
        
        return jsn

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
            contract = self.parseContractParm(fields)

            # https://interactivebrokers.github.io/tws-api/historical_bars.html
            # The request's end date and time (the empty string indicates current present moment).
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
                        results.append(q.__dict__)
                    elif isinstance(q, HistogramDataList):
                        for hd in q:
                            results.append(hd.__dict__)
                    else:
                        results.append(q)
                    self.IBKApp.Queue.remove(q)
                jsn = json.dumps(results)
            elif self.IBKApp.Msg[reqId] == "error":
                jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
            self.send_response(200)            
            pass
        if self.path == "/ContractDetails":
            print("Calling ContractDetails...")
            contract = Contract()
            contract.symbol = ""
            contract.secType = ""
            contract.currency = ""
            contract.exchange = ""
            if "symbol" in fields:
                contract.symbol = str(fields["symbol"][0])
            if "secType" in fields:
                contract.secType = str(fields["secType"][0])
            if "currency" in fields:
                contract.currency = str(fields["currency"][0])
            if "exchange" in fields:
                contract.exchange = str(fields["exchange"][0])
            if "lastTradeDateOrContractMonth" in fields:
                contract.lastTradeDateOrContractMonth = str(fields["lastTradeDateOrContractMonth"][0])
            if "localSymbol" in fields:
                contract.localSymbol = str(fields["localSymbol"][0])
            
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
                    print("Response length: {}".format(len(tempQueue)))
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

                                for k in con.keys():
                                    if "decimal.Decimal" in str(type(con[k])):
                                        con[k] = float(con[k])
                                    if isinstance(con[k], dict):
                                        for c in con[k]:
                                            if "decimal.Decimal" in str(type(con[k][c])):
                                                con[k][c] = float(con[k][c])

                                try:
                                    results.append(json.dumps(con))
                                except Exception as ex:
                                    print(f"  File \"{__file__}\", line {sys.exc_info()[2].tb_frame.f_lineno}, in {__name__}")
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
        if self.path == "/Search":
            term = ""
            if "term" in fields:
                term = str(fields["term"][0])

            hsh = "{}".format(term) + "{}".format(datetime.date.today())

            if hsh in self.Cache:
                print("Using cache: {}".format(hsh))
                jsn = self.Cache[hsh]
            else:
                reqId = 211
                self.IBKApp.Msg[reqId] = "running"
                self.IBKApp.reqMatchingSymbols(reqId, term)

                timeout = self.waitForResponse(reqId)

                results = []
                if self.IBKApp.Msg[reqId] == "success":
                    # might need to change the Queue to index the request id
                    tempQueue = self.IBKApp.Queue.copy()
                    for q in tempQueue:
                        if isinstance(q, ContractDescription):
                            conDets = q.__dict__
                            if "contract" in conDets:
                                con = conDets["contract"].__dict__
                                del conDets["contract"]
                                derivativeSecTypes = conDets["derivativeSecTypes"]
                                del conDets["derivativeSecTypes"]
                                con["details"] = conDets
                                con["derivativeSecTypes"] = "{}".format(derivativeSecTypes)

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
                    jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop(), "timeout": timeout})
                elif timeout:
                    jsn = json.dumps({"status":"timeout"})
            
            self.send_response(200)
            pass
        if self.path == "/Balance":
            reqId = 9001
            self.IBKApp.Msg[reqId] = "running"
            
            self.IBKApp.reqAccountSummary(reqId, "All", AccountSummaryTags.AllTags)

            timeout = self.waitForResponse(reqId)

            results = []
            if self.IBKApp.Msg[reqId] == "success":
                tempQueue = self.IBKApp.Queue.copy()
                for q in tempQueue:
                    print(f" -- {q} ")
                    self.IBKApp.Queue.remove(q)
            elif self.IBKApp.Msg[reqId] == "error":
                jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop(), "timeout": timeout})
            elif timeout:
                jsn = json.dumps({"status":"timeout"})
            self.send_response(200)
            pass
        if self.path == "/Positions":
            reqId = 6001
            self.IBKApp.Msg[reqId] = "running"
            
            self.IBKApp.reqPositions()

            timeout = self.waitForResponse(reqId)

            results = []
            if self.IBKApp.Msg[reqId] == "success":
                tempQueue = self.IBKApp.Queue.copy()
                for q in tempQueue:
                    print(f" -- {q} ")
                    self.IBKApp.Queue.remove(q)
            elif self.IBKApp.Msg[reqId] == "error":
                jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop(), "timeout": timeout})
            elif timeout:
                jsn = json.dumps({"status":"timeout"})
            self.send_response(200)
            pass
        if self.path == "/OrderBook":
            contract = self.parseContractParm(fields)
            depth = 1
            if "depth" in fields:
                depth = int(fields["depth"][0])
            
            print("orderbook: {}".format(contract))
            reqId = 2001
            # queryTime the period for which to get ticks
            self.IBKApp.Msg[reqId] = "running"
            self.IBKApp.reqMktDepth(reqId, contract, depth, False, [])

            results = []
            timeout = self.waitForResponse(reqId)
            
            if self.IBKApp.Msg[reqId] == "success":
                tempQueue = self.IBKApp.Queue.copy()
                for q in tempQueue:
                    results.append(q)
                    self.IBKApp.Queue.remove(q)
                jsn = json.dumps(results)
            elif self.IBKApp.Msg[reqId] == "error":
                jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
            self.send_response(200)
            self.IBKApp.cancelMktDepth(2001, False)
            pass
        if self.path == "/Order":
            contract = self.parseContractParm(fields)
            price = 0
            if "price" in fields:
                price = int(fields["price"][0])
            qty = 0
            if "qty" in fields:
                qty = int(fields["qty"][0])
            action = "" # BuY, SELL
            if "action" in fields:
                action = str(fields["action"][0])
            _type = ""
            if "type" in fields:
                _type = str(fields["type"][0])
            id = ""
            if "id" in fields:
                id = str(fields["id"][0])
            
            if _type == "LIMIT":
                jsn = self.placeLimitOrder(contract, price, qty, action)
            if _type == "CANCEL":
                jsn = self.cancleOrder(id)
            print("order: {}".format(contract))
            pass
        if self.path == "/Orders":
            contract = self.parseContractParm(fields)
            _type = ""
            if "type" in fields:
                _type = str(fields["type"][0])
            if _type == "OPEN":
                jsn = self.getOpenOrders()
            if _type == "CLOSED":
                jsn = self.getClosedOrders()
            print("Orders {} requested".format(_type))
            pass
        if self.path == "/MktData":
            # parse params
            contract = self.parseContractParm(fields)
            
            print("constract: {}".format(contract))
            reqId = 1000
            # queryTime the period for which to get ticks
            self.IBKApp.Msg[reqId] = "running"
            self.reqMktData(reqId, contract, "", False, False, [])
            results = []
            timeout = self.waitForResponse(reqId)
            
            if self.IBKApp.Msg[reqId] == "success":
                self.cancelMktData(reqId)
                tempQueue = self.IBKApp.Queue.copy()
                for q in tempQueue:
                    if isinstance(q, BarData):
                        results.append(q.__dict__)
                    elif isinstance(q, HistogramDataList):
                        for hd in q:
                            results.append(hd.__dict__)
                    else:
                        results.append(q)
                    self.IBKApp.Queue.remove(q)
                jsn = json.dumps(results)
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