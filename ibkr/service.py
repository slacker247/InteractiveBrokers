"""
Copyright (C) 2019 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
 and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.
"""

import argparse
import datetime
import collections
import inspect

import socket
import threading
import logging
import time
import os.path
import sys
import ssl

db_import = os.path.join(sys.path[0], "C:\\TWS API\\source\\pythonclient")
print(db_import)
sys.path.insert(1, db_import)

from ibapi import wrapper
from ibapi import utils
from ibapi.client import EClient
from ibapi.utils import iswrapper

# types
from ibapi.common import * # @UnusedWildImport
from ibapi.order_condition import * # @UnusedWildImport
from ibapi.contract import * # @UnusedWildImport
from ibapi.order import * # @UnusedWildImport
from ibapi.order_state import * # @UnusedWildImport
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.commission_report import CommissionReport
from ibapi.ticktype import * # @UnusedWildImport
from ibapi.tag_value import TagValue

from ibapi.account_summary_tags import *

#from ContractSamples import ContractSamples
#from OrderSamples import OrderSamples
#from AvailableAlgoParams import AvailableAlgoParams
#from ScannerSubscriptionSamples import ScannerSubscriptionSamples
#from FaAllocationSamples import FaAllocationSamples
from ibapi.scanner import ScanData

from http.server import HTTPServer
from Activity import Activity
from TestApp import TestApp
from server import Server

def SetupLogger():
    if not os.path.exists("log"):
        os.makedirs("log")

    time.strftime("pyibapi.%Y%m%d_%H%M%S.log")

    recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'

    timefmt = '%y%m%d_%H:%M:%S'

    # logging.basicConfig( level=logging.DEBUG,
    #                    format=recfmt, datefmt=timefmt)
    logging.basicConfig(filename=time.strftime("log/pyibapi.%y%m%d_%H%M%S.log"),
                        filemode="w",
                        level=logging.INFO,
                        format=recfmt, datefmt=timefmt)
    logger = logging.getLogger()
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    logger.addHandler(console)

def printinstance(inst:Object):
    attrs = vars(inst)
    print(', '.join("%s: %s" % item for item in attrs.items()))

# this is here for documentation generation
"""
#! [ereader]
        # You don't need to run this in your code!
        self.reader = reader.EReader(self.conn, self.msg_queue)
        self.reader.start()   # start thread
#! [ereader]
"""

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

def main():
    SetupLogger()
    logging.debug("now is %s", datetime.datetime.now())
    logging.getLogger().setLevel(logging.ERROR)

    cmdLineParser = argparse.ArgumentParser("api tests")
    # cmdLineParser.add_option("-c", action="store_True", dest="use_cache", default = False, help = "use the cache")
    # cmdLineParser.add_option("-f", action="store", type="string", dest="file", default="", help="the input file")
    cmdLineParser.add_argument("-p", "--port", action="store", type=int,
                               dest="port", default=7497, help="The TCP port to use")
    cmdLineParser.add_argument("-C", "--global-cancel", action="store_true",
                               dest="global_cancel", default=False,
                               help="whether to trigger a globalCancel req")
    args = cmdLineParser.parse_args()
    print("Using args", args)
    logging.debug("Using args %s", args)
    # print(args)


    # enable logging when member vars are assigned
    from ibapi import utils
    Order.__setattr__ = utils.setattr_log
    Contract.__setattr__ = utils.setattr_log
    DeltaNeutralContract.__setattr__ = utils.setattr_log
    TagValue.__setattr__ = utils.setattr_log
    TimeCondition.__setattr__ = utils.setattr_log
    ExecutionCondition.__setattr__ = utils.setattr_log
    MarginCondition.__setattr__ = utils.setattr_log
    PriceCondition.__setattr__ = utils.setattr_log
    PercentChangeCondition.__setattr__ = utils.setattr_log
    VolumeCondition.__setattr__ = utils.setattr_log

    # from inspect import signature as sig
    # import code code.interact(local=dict(globals(), **locals()))
    # sys.exit(1)

    # tc = TestClient(None)
    # tc.reqMktData(1101, ContractSamples.USStockAtSmart(), "", False, None)
    # print(tc.reqId2nReq)
    # sys.exit(1)


    print(ssl.OPENSSL_VERSION)
    webServer = None
    th = None
    try:
        app = TestApp()
        Server.IBKApp = app
        ip = extract_ip()
        webServer = HTTPServer((ip, 8080), Server)

        # Modern TLS context setup
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

        # Wrap the socket using context
        webServer.socket = context.wrap_socket(webServer.socket, server_side=True)

        if args.global_cancel:
            app.globalCancelOnly = True
        print(f"Server listening on https://{ip}:8080")
        th = threading.Thread(target=webServer.serve_forever)
        th.start()

        # ! [connect]
        app.connect("127.0.0.1", args.port, clientId=0)
        # ! [connect]
        print(f"serverVersion:{app.serverVersion()} connectionTime:{app.twsConnectionTime()}")

        # ! [clientrun]
        app.run()
        # ! [clientrun]
    except:
        raise
    finally:
        webServer.server_close()
        th.join()
        app.dumpTestCoverageSituation()
        app.dumpReqAnsErrSituation()


if __name__ == "__main__":
    main()
