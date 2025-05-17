from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sys
import re
import socket
import json
import subprocess
import ssl

HOST = 'localhost'
PORT = 8080

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

def full_stack():
    import traceback, sys
    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
    if exc is not None:  # i.e. an exception is present
        del stack[-1]       # remove call of full_stack, the printed exception
                            # will contain the caught exception caller instead
    trc = 'Traceback (most recent call last):\n'
    stackstr = trc + ''.join(traceback.format_list(stack))
    if exc is not None:
         stackstr += '  ' + traceback.format_exc().lstrip(trc)
    return stackstr

def command(cmd, work_dir=None, showOutput=False):
    # f"bash -c '{cmd}'"
    process = subprocess.Popen(cmd,
                    cwd=work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True)
    lines = []
    if showOutput:
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline().decode()
            if nextline == '' and process.poll() is not None:
                break
            lines.append(nextline)
            sys.stdout.write(nextline)
            sys.stdout.flush()
    syms, err = process.communicate()
    if len(syms) == 0:
        syms = "\n".join(lines)
    exitCode = process.returncode
    return syms, err, exitCode

class AccountSummaryHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            # Request summary (blocking call)
            cmd = "python -u handler.py GET " + self.path
            syms, err, exitCode = command(cmd)
            output = syms.decode("utf-8")
            jsn = ""
            lines = output.split("\n")
            idx = 0
            while idx < len(lines):
                line = lines[idx].strip()
                print(line)
                try:
                    jsn = json.loads(line)
                except:
                    pass
                idx += 1
            print(jsn)
            response = json.dumps(jsn)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(bytes(response, "utf-8"))

        except Exception as e:
            print(full_stack())
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = json.dumps({'error': str(e)}).encode('utf-8')
            self.wfile.write(error_msg)

    def do_POST(self):
        length = int(self.headers['content-length'])
        field_data = self.rfile.read(length).decode("utf-8")

        with open("post.json", "w") as f:
            f.write(field_data)
        try:
            # Request summary (blocking call)
            cmd = "python -u handler.py POST " + self.path
            syms, err, exitCode = command(cmd)
            output = syms.decode("utf-8")
            print(output)
            jsn = ""
            lines = output.split("\n")
            idx = 0
            while idx < len(lines):
                line = lines[idx].strip()
                print(line)
                try:
                    jsn = json.loads(line)
                except:
                    pass
                idx += 1
            print(jsn)
            response = json.dumps(jsn)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(bytes(response, "utf-8"))

        except Exception as e:
            print(full_stack())
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = json.dumps({'error': str(e)}).encode('utf-8')
            self.wfile.write(error_msg)

    def do_DELETE(self):
        try:
            # Request summary (blocking call)
            cmd = "python -u handler.py DELETE " + self.path
            syms, err, exitCode = command(cmd)
            output = syms.decode("utf-8")
            print(output)
            if "error" in output:
                raise Exception(output)
            jsn = json.loads(output)
            response = json.dumps(jsn)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(bytes(response, "utf-8"))

        except Exception as e:
            print(full_stack())
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = json.dumps({'error': str(e)}).encode('utf-8')
            self.wfile.write(error_msg)

def run_server():
    HOST = extract_ip()
    server = HTTPServer((HOST, PORT), AccountSummaryHandler)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="ibkr\\cert.pem", keyfile="ibkr\\key.pem")

    # Wrap the socket using context
    server.socket = context.wrap_socket(server.socket, server_side=True)

    print(f"Serving on http://{HOST}:{PORT}")
    server.serve_forever()


# === Models ===
class OrderRequest():
    symbol: str
    exchange: str = 'SMART'
    currency: str = 'USD'
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: float = None  # for LIMIT order
    orderType: str = 'LMT'  # 'LMT' or 'MKT'

class CancelRequest():
    orderId: int

# === Routes ===

'''
@app.get("/v1/api/iserver/account/{account}/summary")
def get_account_balance(account: str):
    summary = None  # Now you have the actual data    

    # Prepare mapping from tag to field name (Web API keys)
    tag_map = {
        "AccountType": "accountType",
        "AvailableFunds": "availableFunds",
        "SMA": "SMA",
        "BuyingPower": "buyingPower",
        "ExcessLiquidity": "excessLiquidity",
        "NetLiquidation": "netLiquidationValue",
        "EquityWithLoanValue": "equityWithLoanValue",
        "RegTEquity": "regTLoan",
        "TotalCashValue": "totalCashValue",
        "AccruedCash": "accruedInterest",
        "InitMarginReq": "initialMargin",
        "MaintMarginReq": "maintenanceMargin",
    }

    result = {key: None for key in tag_map.values()}
    cash_balances = {}

    # Extract values
    for item in summary:
        if item.tag in tag_map:
            key = tag_map[item.tag]
            try:
                result[key] = float(item.value)
            except ValueError:
                result[key] = item.value
        # Build cashBalances by currency if available
        if item.tag == "Currency":
            # This tag appears in currency-specific entries
            currency = item.currency
            cash_balances[currency] = {"currency": currency, "balance": None, "settledCash": None}
        if item.tag == "CashBalance":
            currency = item.currency
            try:
                cash_balances[currency]["balance"] = float(item.value)
            except Exception:
                cash_balances[currency]["balance"] = None
        if item.tag == "SettledCash":
            currency = item.currency
            try:
                cash_balances[currency]["settledCash"] = float(item.value)
            except Exception:
                cash_balances[currency]["settledCash"] = None

    # Fallback fields
    result["accountType"] = result.get("accountType") or "UNKNOWN"
    result["status"] = "Active"  # no direct equivalent, defaulting

    # Convert cash_balances dict to list
    cash_balances_list = list(cash_balances.values())
    if cash_balances_list:
        result["cashBalances"] = cash_balances_list
    else:
        result["cashBalances"] = []

    # Provide balance field (sum of availableFunds or netLiquidationValue as fallback)
    result["balance"] = result.get("availableFunds") or result.get("netLiquidationValue") or 0.0

    return result

@app.get("/account/positions")
def get_positions():
    return [
        {
            'symbol': pos.contract.symbol,
            'quantity': pos.position,
            'avgCost': pos.avgCost,
            'marketPrice': pos.marketPrice,
        }
        for pos in ib.positions()
    ]

@app.get("/market/orderbook/{symbol}")
def get_order_book(symbol: str):
    contract = Stock(symbol, 'SMART', 'USD')
    ib.qualifyContracts(contract)
    book = ib.reqMktDepth(contract)
    ib.sleep(1)
    data = [{'side': row.side, 'price': row.price, 'size': row.size} for row in book.domBids + book.domAsks]
    ib.cancelMktDepth(contract)
    return data

@app.post("/order/place")
def place_order(req: OrderRequest):
    contract = Stock(req.symbol, req.exchange, req.currency)
    ib.qualifyContracts(contract)
    if req.orderType == 'LMT' and req.price is None:
        raise HTTPException(status_code=400, detail="Limit order requires a price.")
    order_class = LimitOrder if req.orderType == 'LMT' else MarketOrder
    order = order_class(req.side.upper(), req.quantity, req.price) if req.orderType == 'LMT' else order_class(req.side.upper(), req.quantity)
    trade = ib.placeOrder(contract, order)
    ib.sleep(1)
    return {
        "orderId": trade.order.orderId,
        "status": trade.orderStatus.status
    }

@app.get("/order/status/{order_id}")
def get_order_status(order_id: int):
    orders = ib.orders()
    for o in orders:
        if o.orderId == order_id:
            return {
                "orderId": o.orderId,
                "status": o.orderStatus.status,
                "filled": o.orderStatus.filled,
                "remaining": o.orderStatus.remaining
            }
    raise HTTPException(status_code=404, detail="Order not found")

@app.post("/order/cancel")
def cancel_order(req: CancelRequest):
    orders = ib.orders()
    for o in orders:
        if o.orderId == req.orderId:
            ib.cancelOrder(o)
            return {"status": "cancelled"}
    raise HTTPException(status_code=404, detail="Order not found")

@app.post("/order/sell")
def place_sell_order(req: OrderRequest):
    req.side = 'SELL'
    return place_order(req)

@app.get("/account/order_history")
def get_order_history():
    trades = ib.trades()
    return [{
        'orderId': t.order.orderId,
        'symbol': t.contract.symbol,
        'side': t.order.action,
        'quantity': t.order.totalQuantity,
        'filled': t.orderStatus.filled,
        'status': t.orderStatus.status,
        'price': t.order.lmtPrice if hasattr(t.order, 'lmtPrice') else None
    } for t in trades]

@app.get("/account/transactions")
def get_transactions():
    executions = ib.executions()
    return [{
        'execId': e.execId,
        'symbol': e.contract.symbol,
        'side': e.side,
        'price': e.price,
        'qty': e.shares,
        'time': e.time.isoformat()
    } for e in executions]
'''
if __name__ == '__main__':
    run_server()


