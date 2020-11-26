import os.path
import sys

db_import = os.path.join(sys.path[0], "C:\\TWS API\\source\\pythonclient")
print(db_import)
sys.path.insert(1, db_import)

from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import datetime

from ibapi.common import * # @UnusedWildImport
from ibapi.contract import * # @UnusedWildImport
from TestApp import TestApp

hostName = "localhost"
serverPort = 8080

class Server(BaseHTTPRequestHandler):
    IBKApp = None

    def do_POST(self):
        if self.path == "/Ticks":
            # parse params
            contract = Contract()
            contract.symbol = "EUR"
            contract.secType = "CASH"
            contract.currency = "GBP"
            contract.exchange = "IDEALPRO"

            reqId = 4102
            # queryTime the period for which to get ticks
            queryTime = (datetime.datetime.today() - datetime.timedelta(days=180)).strftime("%Y%m%d %H:%M:%S")
            self.IBKApp.Msg[reqId] = "running"
            self.IBKApp.reqHistoricalData(reqId, contract, queryTime,
                               "1 M", "1 day", "MIDPOINT", 1, 1, False, [])
            results = []
            found = False
            timeout = False
            start = datetime.datetime.now()
            while(not found and not timeout):
                time.sleep(0.12)
                if not self.IBKApp.Msg[reqId] == "running":
                    found = True
                if datetime.datetime.now() - start > datetime.timedelta(minutes=2):
                    timeout = True
            
            if self.IBKApp.Msg[reqId] == "success":
                tempQueue = self.IBKApp.Queue.copy()
                for q in tempQueue:
                    if q is BarData:
                        results.append(q)
                    elif q is HistogramDataList:
                        for hd in q:
                            results.append(hd)
                    else:
                        results.append(q)
                    self.IBKApp.Queue.remove(q)
                jsn = "{}".format(results)
            elif self.IBKApp.Msg[reqId] == "error":
                jsn = json.dumps({"status":"error", "msg":self.IBKApp.Queue.pop()})
                
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(jsn, "utf-8"))
            pass
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