import threading
from ib_insync import IB
import queue
import asyncio

class IBWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.ib = IB()
        self.requests = queue.Queue()
        self.daemon = True

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.ib.connect('127.0.0.1', 7497, clientId=123)
        while True:
            method, args, response_q = self.requests.get()
            try:
                if method == 'accountSummary':
                    response = self.ib.accountSummary()
                    response_q.put(response)
                if method == 'positions':
                    response = self.ib.positions()
                    response_q.put(response)
                if method == 'reqContractDetails':
                    response = self.ib.reqContractDetails(*args)
                    response_q.put(response)
                if method == 'reqMktData':
                    response = self.ib.reqMktData(*args)
                    response_q.put(response)
                if method == 'qualifyContracts':
                    response = self.ib.qualifyContracts(*args)
                    response_q.put(response)
                if method == 'placeOrder':
                    response = self.ib.placeOrder(*args)
                    response_q.put(response)
                if method == 'reqOpenOrders':
                    response = self.ib.reqOpenOrders()
                    response_q.put(response)
                if method == 'cancelOrder':
                    response = self.ib.cancelOrder(*args)
                    response_q.put(response)
                if method == 'reqGlobalCancel':
                    response = self.ib.reqGlobalCancel()
                    response_q.put(response)
                if method == 'trades':
                    response = self.ib.trades()
                    response_q.put(response)
                if method == 'reqMatchingSymbols':
                    response = self.ib.reqMatchingSymbols(*args)
                    response_q.put(response)
                if method == 'reqHistoricalData':
                    response = self.ib.reqHistoricalData(*args)
                    response_q.put(response)
            except Exception as e:
                print(f"IBWorker - run - {e}")
                print(args)
                response_q.put(e)

    def request(self, method, *args):
        response_q = queue.Queue()
        self.requests.put((method, args, response_q))
        result = response_q.get()
        if isinstance(result, Exception):
            raise result
        return result

ib_worker = IBWorker()
ib_worker.start()


