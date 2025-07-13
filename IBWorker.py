import threading
from ib_insync import IB
import queue
import asyncio

class IBWorker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.ib = IB()
        self.requests = queue.Queue()
        self.error_messages = queue.Queue()  # Captured error messages
        self.daemon = True
        self.running = False
        self.ib.errorEvent += self.on_error  # Attach error handler

    def on_error(self, reqId, errorCode, errorString, contract):
        """Store errors in a thread-safe queue."""
        self.error_messages.put({
            'reqId': reqId,
            'errorCode': errorCode,
            'errorString': errorString,
            'contract': contract
        })

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=123)
            self.running = True
        except Exception as ex:
            print(ex)
            self.error_messages.put({'error': str(ex)})
            return  # Exit thread if unable to connect

        while self.running:
            method, args, response_q = self.requests.get()
            print(*args)
            try:
                response = None
                if method == 'accountSummary':
                    response = self.ib.accountSummary(args[0])
                    response_q.put(response)
                if method == 'positions':
                    response = self.ib.positions()
                    response_q.put(response)
                if method == 'reqContractDetails':
                    response = self.ib.reqContractDetails(args[0])
                    response_q.put(response)
                if method == 'reqMktData':
                    response = self.ib.reqMktData(args[0], args[1], args[2], args[3])
                    response_q.put(response)
                if method == 'qualifyContracts':
                    response = self.ib.qualifyContracts(args[0])
                    response_q.put(response)
                if method == 'placeOrder':
                    response = self.ib.placeOrder(args[0], args[1])
                    response_q.put(response)
                if method == 'reqOpenOrders':
                    response = self.ib.reqOpenOrders()
                    response_q.put(response)
                if method == 'cancelOrder':
                    response = self.ib.cancelOrder(args[0])
                    response_q.put(response)
                if method == 'reqGlobalCancel':
                    response = self.ib.reqGlobalCancel()
                    response_q.put(response)
                if method == 'trades':
                    response = self.ib.trades()
                    response_q.put(response)
                if method == 'reqMatchingSymbols':
                    response = self.ib.reqMatchingSymbols(args[0])
                    response_q.put(response)
                if method == 'reqHistoricalData':
                    response = self.ib.reqHistoricalData(args[0], args[1], args[2], args[3], args[4], args[5], args[6])
                    response_q.put(response)
                if response == None:
                    raise ValueError(f"Unknown method: {method}")
            except Exception as e:
                print(f"IBWorker - run - {e}")
                print(args)
                self.error_messages.put({'error': str(e), 'args': args})
                response_q.put(e)

    def request(self, method, *args):
        response_q = queue.Queue()
        self.requests.put((method, args, response_q))
        result = response_q.get()
        if isinstance(result, Exception):
            raise result
        return result

    def get_errors(self):
        """Retrieve all pending errors."""
        errors = []
        while not self.error_messages.empty():
            errors.append(self.error_messages.get())
        return errors

ib_worker = IBWorker()
ib_worker.start()


