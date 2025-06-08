import socket
import signal
import sys
import inspect
from datetime import datetime
import json
import re
import time
import threading
import asyncio
import IBWorker
# https://ib-insync.readthedocs.io/api.html
from ib_insync import *
import tracemalloc
tracemalloc.start()
ib = None
server_socket = None
threads = []

def shutdown(signum, frame):
    global server_socket, threads
    print("\nShutting down gracefully...")
    if server_socket:
        server_socket.close()
    for t in threads:
        t.join(timeout=1)
    sys.exit(0)

# Register Ctrl+C handler
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

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

def parse_account_summary(summary):
    def get(tag):
        item = next((i for i in summary if i.tag == tag), None)
        return float(item.value) if item and item.value.replace('.', '', 1).replace('-', '', 1).isdigit() else item.value if item else None

    cash_balances = {}
    for item in summary:
        if item.tag == 'CashBalance':
            currency = item.currency
            cash_balances[currency] = {
                'currency': currency,
                'balance': float(item.value),
                'settledCash': float(item.value)
            }

    total_usd = cash_balances.get("USD", {"balance": 0})["balance"]
    cash_balances["Total (in USD)"] = {
        "currency": "Total (in USD)",
        "balance": total_usd,
        "settledCash": total_usd
    }

    return {
        "accountType": get("AccountType"),
        "status": "active",
        "balance": get("AvailableFunds"),
        "SMA": get("SMA"),
        "buyingPower": get("BuyingPower"),
        "availableFunds": get("AvailableFunds"),
        "excessLiquidity": get("ExcessLiquidity"),
        "netLiquidationValue": get("NetLiquidation"),
        "equityWithLoanValue": get("EquityWithLoanValue"),
        "regTLoan": get("RegTEquity"),
        "securitiesGVP": get("GrossPositionValue"),
        "totalCashValue": get("TotalCashValue"),
        "accruedInterest": get("AccruedCash"),
        "regTMargin": get("RegTMargin"),
        "initialMargin": get("InitialMarginRequirement"),
        "maintenanceMargin": get("MaintenanceMarginRequirement"),
        "cashBalances": list(cash_balances.values())
    }

def get_account_summary(account_id):
    summary = {}
    summary = IBWorker.ib_worker.request('accountSummary')
    parsed = parse_account_summary(summary)
    return parsed

def post_handler(path, post_data):
    return {"status": "POST not implemented for path", "path": path, "data": post_data}

def get_positions(
    accountId: str, 
    pageId: int, 
    model: str = None, 
    sort: str = 'name', 
    direction: str = 'a', 
    waitForSecDef: bool = False
):
    """
    Fetch positions from IB, filter by accountId, sort and paginate.
    """

    # Request positions (note: ib.positions() returns a list of (contract, position, avgCost) tuples)
    # positions() does not filter by account, so filter here.
    all_positions = IBWorker.ib_worker.request('positions')

    # Filter by accountId
    positions_filtered = [
        (contract, pos, avgCost) for (account, contract, pos, avgCost) in all_positions if account == accountId
    ]

    # If waitForSecDef is True, fetch security definitions for all contracts
    if waitForSecDef:
        for contract, _, _ in positions_filtered:
            IBWorker.ib_worker.request('reqContractDetails', contract)

    # Convert positions to output dicts like your format
    result = []
    for contract, position, avgCost in positions_filtered:
        # Get market price
        ticker = IBWorker.ib_worker.request('reqMktData', contract, "", False, False)
        time.sleep(0.1)  # brief wait to get market data

        # Build response dict (some fields from contract, others from ib_insync calls)
        d = {
            "acctId": accountId,
            "conid": contract.conId,
            "contractDesc": contract.localSymbol or contract.symbol,
            "position": position,
            "mktPrice": ticker.marketPrice() if ticker.marketPrice() is not None else 0,
            "mktValue": position * (ticker.marketPrice() or 0),
            "currency": contract.currency,
            "avgCost": avgCost,
            "avgPrice": avgCost,
            "realizedPnl": 0,      # ib_insync does not provide realized pnl here
            "unrealizedPnl": 0,    # requires more calculation, omitted for now
            "exchs": None,
            "expiry": getattr(contract, 'lastTradeDateOrContractMonth', None),
            "putOrCall": getattr(contract, 'right', None),
            "multiplier": getattr(contract, 'multiplier', 0) or 0,
            "strike": str(getattr(contract, 'strike', '0')),
            "exerciseStyle": None,
            "conExchMap": [],
            "assetClass": getattr(contract, 'secType', ''),
            "undConid": getattr(contract, 'underConId', 0) or 0,
            "model": model or "",
            "incrementRules": [
                {
                    "lowerEdge": 0,
                    "increment": 0.01 if contract.secType != 'CRYPTO' else 0.25
                }
            ],
            "displayRule": {
                "magnification": 0,
                "displayRuleStep": [
                    {
                        "decimalDigits": 2,
                        "lowerEdge": 0,
                        "wholeDigits": 4
                    }
                ]
            },
            "time": 0,
            "chineseName": None,
            "allExchanges": getattr(contract, 'exchange', ''),
            "listingExchange": getattr(contract, 'exchange', ''),
            "countryCode": None,
            "name": contract.localSymbol or contract.symbol,
            "lastTradingDay": getattr(contract, 'lastTradeDateOrContractMonth', None),
            "group": None,
            "sector": None,
            "sectorGroup": None,
            "ticker": contract.symbol,
            "type": "",
            "hasOptions": False,
            "fullName": contract.symbol,
            "isEventContract": False,
            "pageSize": 100
        }
        result.append(d)

    # Sort by specified field
    reverse = (direction == 'd')
    result.sort(key=lambda x: x.get(sort, ""), reverse=reverse)

    # Paginate
    page_size = 100
    start = pageId * page_size
    end = start + page_size
    return result[start:end]

def post_order(account_id, orders_data):
    results = []

    for data in orders_data:
        account = data.get('acctId') or data.get('accountId')
        conid = data['conid']
        sec_type = data.get('secType', 'STK')
        order_type = data['orderType']
        side = data['side']
        tif = data['tif']
        quantity = data['quantity']
        price = data.get('price')
        aux_price = data.get('auxPrice')
        symbol = data.get('ticker', '')
        exchange = "SMART" #data.get('listingExchange', 'SMART')  This order will be directly routed to NASDAQ. Direct routed orders may result in higher trade fees. Restriction is specified in Precautionary Settings of Global Configuration/API
        currency = 'USD'  # Assuming USD; customize if needed

        contract = Contract(conId=conid, symbol=symbol, secType=sec_type, exchange=exchange, currency=currency)

        order = Order(
            action=side,
            orderType=order_type,
            totalQuantity=quantity,
            tif=tif,
            lmtPrice=price,
            auxPrice=aux_price,
            outsideRth=data.get('outsideRTH', False),
            transmit=True
        )

        # Optional: trailing stop
        if order_type == 'TRAIL':
            order.trailingStopPrice = aux_price
            order.trailingPercent = data['trailingAmt'] if data.get('trailingType') == '%' else None

        # Optional: algo
        if data.get('strategy'):
            order.algoStrategy = data['strategy']
            order.algoParams = [
                TagValue(k, str(v)) for k, v in (data.get('strategyParameters') or {}).items()
            ]

        # Optional: bracket order handling
        if 'parentId' in data:
            order.parentId = data['parentId']

        # Place order
        IBWorker.ib_worker.request('qualifyContracts', contract)
        trade = IBWorker.ib_worker.request('placeOrder', contract, order)
        time.sleep(1)  # give time for order to register

        results.append({
            "order_id": str(trade.order.orderId),
            "order_status": trade.orderStatus.status,
            "encrypt_message": "1"  # Mocked for format compatibility
        })

    return results

def delete_order(account_id, order_id):
    # Try to cancel the order
    try:
        orders = IBWorker.ib_worker.request('reqOpenOrders')
        order_found = None
        for t in orders:
            if t.order.orderId == order_id:
                order_found = t

        if order_found:
            IBWorker.ib_worker.request('cancelOrder', order_found.order)
            response = [{
                "msg": "Request was submitted",
                "order_id": str(order_id),
                "order_status": order_found.orderStatus.status,
                "encrypt_message": "1"
            }]
        else:
            response = [{
                "msg": "Order not found or already executed",
                "order_id": str(order_id),
                "order_status": "Unknown",
                "encrypt_message": "0"
            }]
    except Exception as e:
        response = [{
            "msg": f"Error occurred: {str(e)}",
            "order_id": str(order_id),
            "order_status": "Failed",
            "encrypt_message": "0"
        }]

    return response

def format_order(trade:Trade):
    # Simulate a mapping for demonstration purposes
    return {
        "acct": trade.order.account,
        "exchange": trade.contract.exchange,
        "conidex": f"{trade.contract.conId}@{trade.contract.exchange}",
        "conid": trade.contract.conId,
        "account": trade.order.account,
        "orderId": trade.order.orderId,
        "cashCcy": getattr(trade.contract, 'currency', 'USD'),
        "sizeAndFills": f"{trade.order.totalQuantity} {trade.contract.currency}",
        "orderDesc": f"{trade.order.action.title()} {trade.order.totalQuantity} {trade.order.orderType.title()} {trade.order.lmtPrice}, {trade.order.tif}",
        "description1": trade.contract.localSymbol or trade.contract.symbol,
        "ticker": trade.contract.symbol,
        "secType": trade.contract.secType,
        "listingExchange": trade.contract.exchange,
        "remainingQuantity": trade.orderStatus.remaining,
        "filledQuantity": trade.orderStatus.filled,
        "totalSize": trade.order.totalQuantity,
        "totalCashSize": getattr(trade.order, 'totalCashSize', 0),
        "companyName": getattr(trade.contract, 'longName', trade.contract.symbol),
        "status": trade.orderStatus.status,
        "order_ccp_status": trade.orderStatus.status,
        "origOrderType": trade.order.orderType,
        "supportsTaxOpt": "0",
        "lastExecutionTime": "",
        "orderType": trade.order.orderType.title(),
        "bgColor": "#FFFFFF",
        "fgColor": "#000000",
        "isEventTrading": "0",
        "price": str(trade.order.lmtPrice),
        "timeInForce": trade.order.tif,
        "lastExecutionTime_r": 0,
        "side": trade.order.action,
        "avgPrice": str(trade.orderStatus.avgFillPrice or "")
    }

def get_orders(filters: list, force: bool, account_id: str):

    if force:
        IBWorker.ib_worker.request('reqGlobalCancel')

    time.sleep(0.5)  # Let it clear

    open_orders = IBWorker.ib_worker.request('reqOpenOrders')
    time.sleep(0.5)
    trades = IBWorker.ib_worker.request('trades')

    # Merge open and completed orders
    all_orders = trades + open_orders

    # Deduplicate by orderId
    seen = set()
    deduped_orders = []
    for t in all_orders:
        if t.order.orderId not in seen:
            seen.add(t.order.orderId)
            deduped_orders.append(t)

    # Filter by accountId
    if account_id:
        deduped_orders = [t for t in deduped_orders if t.order.account == account_id]

    # Filter by status
    if filters:
        filters_set = set(f.lower() for f in filters if f.lower() != "sortbytime")
        deduped_orders = [
            t for t in deduped_orders if t.orderStatus.status.lower() in filters_set
        ]

    # Sort if requested
    if filters and "sortbytime" in [f.lower() for f in filters]:
        deduped_orders.sort(key=lambda t: t.order.orderId, reverse=True)

    formatted = [format_order(t) for t in deduped_orders]

    return {
        "orders": formatted,
        "snapshot": True
    }

def extract_order_id(url):
    match = re.match(r'^GET\s+/iserver/account/order/status/(\d+)$', url)
    if not match:
        print("Invalid URL format. Expected: GET /iserver/account/order/status/{orderId}")
        sys.exit(1)
    return int(match.group(1))

def get_order_status(order_id):
    trades = IBWorker.ib_worker.request('trades')
    for trade in trades:
        if trade.order.permId == order_id or trade.order.orderId == order_id:
            order = trade.order
            fill = trade.fills[-1] if trade.fills else None
            status = trade.orderStatus

            con = trade.contract

            return {
                "sub_type": None,
                "request_id": "209",
                "server_id": "0",
                "order_id": order.orderId,
                "conidex": str(con.conId),
                "conid": con.conId,
                "symbol": con.symbol,
                "side": order.action[0],
                "contract_description_1": con.symbol,
                "listing_exchange": con.exchange,
                "option_acct": "c",
                "company_name": con.localSymbol or con.symbol,
                "size": str(status.remaining()) if status else "0.0",
                "total_size": str(order.totalQuantity),
                "currency": con.currency,
                "account": order.account,
                "order_type": order.orderType,
                "cum_fill": str(status.filled if status else 0.0),
                "order_status": status.status if status else "Unknown",
                "order_ccp_status": "2",
                "order_status_description": "Order " + (status.status if status else "Unknown"),
                "tif": order.tif,
                "fg_color": "#FFFFFF",
                "bg_color": "#000000",
                "order_not_editable": True,
                "editable_fields": "",
                "cannot_cancel_order": True,
                "deactivate_order": False,
                "sec_type": con.secType,
                "available_chart_periods": "#R|1",
                "order_description": f"{order.action} {order.totalQuantity} {order.orderType}, {order.tif}",
                "order_description_with_contract": f"{order.action} {order.totalQuantity} {con.symbol} {order.orderType}, {order.tif}",
                "alert_active": 1,
                "child_order_type": "0",
                "order_clearing_account": order.account,
                "size_and_fills": str(status.filled if status else "0"),
                "exit_strategy_display_price": str(fill.execution.price if fill else 0.0),
                "exit_strategy_chart_description": f"{order.action} {order.totalQuantity} @ {fill.execution.price if fill else 0.0}",
                "average_price": str(status.avgFillPrice if status else 0.0),
                "exit_strategy_tool_availability": "1",
                "allowed_duplicate_opposite": True,
                "order_time": order.transmitTime.strftime("%y%m%d%H%M%S") if hasattr(order, "transmitTime") else ""
            }
    return None

def format_search(match):
    contract = match.contract
    return {
        "conid": contract.conId,
        "companyHeader": contract.description,
        "companyName": contract.description,
        "symbol": contract.symbol,
        "description": contract.primaryExchange,
        "restricted": None,
        "fop": None,
        "opt": None,
        "war": None,
        "sections": [
            {"secType": contract.secType}
        ]
    }

def search(symbol):
    matches = IBWorker.ib_worker.request('reqMatchingSymbols', symbol)
    #contract = Stock(symbol, 'SMART', 'USD')
    #matches = IBWorker.ib_worker.request('reqContractDetails', contract)

    contracts = {}
    if matches == None:
        line = inspect.currentframe().f_lineno
        contracts = {"error": f"{line} - handler - search - Empty result"}
    else:
        contracts = [format_search(m) for m in matches]
    return contracts

def contractLookup(conid):
    contract = Contract(conId=conid, exchange='SMART', secType='STK', currency='USD')
    details = IBWorker.ib_worker.request('reqContractDetails', contract)

    if not details:
        raise ValueError(f"No contract details found for conid {conid}")

    detail = details[0]
    contract = detail.contract

    secdef = {
        "secdef": [
            {
                "incrementRules": [
                    {
                        "lowerEdge": 0,
                        "increment": 0.01
                    }
                ],
                "displayRule": {
                    "magnification": 0,
                    "displayRuleStep": [
                        {
                            "decimalDigits": 2,
                            "lowerEdge": 0,
                            "wholeDigits": 4
                        }
                    ]
                },
                "conid": contract.conId,
                "currency": contract.currency,
                "time": 770,  # static as per your example; replace if dynamic
                "chineseName": "",  # not available from IB API
                "allExchanges": detail.marketRuleIds or "",
                "listingExchange": contract.exchange,
                "countryCode": detail.contract.primaryExchange if hasattr(detail.contract, "primaryExchange") else "US",
                "name": detail.longName or contract.symbol,
                "assetClass": contract.secType,
                "expiry": contract.lastTradeDateOrContractMonth if contract.lastTradeDateOrContractMonth else None,
                "lastTradingDay": None,
                "group": "",  # Not available from IBKR API
                "putOrCall": contract.right if contract.right else None,
                "sector": "",  # Not available from IBKR API
                "sectorGroup": "",  # Not available from IBKR API
                "strike": str(contract.strike) if contract.strike else "0",
                "ticker": contract.symbol,
                "undConid": detail.underConId if hasattr(detail, "underConId") else 0,
                "multiplier": int(contract.multiplier) if contract.multiplier else 0,
                "type": "COMMON",  # assumed; IBKR doesn't provide a direct 'type' field
                "hasOptions": detail.evRule != "",  # crude heuristic
                "fullName": detail.longName or contract.symbol,
                "isUS": contract.currency == "USD",
                "isEventContract": False  # not from IBKR; static unless needed
            }
        ]
    }

    return secdef

def get_formatted_bars(conid, end_datetime, duration_str='1 D', bar_size='1 day'):
    # Create contract with only conid
    contract = Contract(conId=conid, exchange='SMART', secType='STK', currency='USD')
    details = IBWorker.ib_worker.request('reqContractDetails', contract)
    
    if not details:
        raise ValueError(f"No contract details found for conid {conid}")

    resolved_contract = details[0].contract
    symbol = resolved_contract.symbol
    company_name = details[0].longName or symbol  # fallback to symbol if longName unavailable

    bars = IBWorker.ib_worker.request('reqHistoricalData',
        resolved_contract,
        endDateTime=end_datetime,
        durationStr=duration_str,
        barSizeSetting=bar_size,
        whatToShow='TRADES',
        useRTH=True,
        formatDate=1
    )

    if not bars:
        return {}

    first_bar = bars[0]
    start_time_str = first_bar.date.replace(' ', '-')
    chart_pan_time = bars[-1].date.replace(' ', '-')
    price_factor = 100

    result = {
        "serverid": "20477",
        "symbol": symbol,
        "text": company_name,
        "priceFactor": price_factor,
        "startTime": start_time_str,
        "high": f"{int(first_bar.high * price_factor)}/{first_bar.volume}/0",
        "low": f"{int(first_bar.low * price_factor)}/{first_bar.volume}/0",
        "timePeriod": "1d",
        "barLength": 86400,
        "mdAvailability": "RpB",
        "outsideRth": False,
        "tradingDayDuration": 1440,
        "volumeFactor": 1,
        "priceDisplayRule": 1,
        "priceDisplayValue": "2",
        "chartPanStartTime": chart_pan_time,
        "direction": -1,
        "negativeCapable": False,
        "messageVersion": 2,
        "travelTime": 48,
        "data": [
            {
                "t": int(time.mktime(datetime.strptime(bar.date.split(' ')[0], "%Y%m%d").timetuple()) * 1000),
                "o": bar.open,
                "c": bar.close,
                "h": bar.high,
                "l": bar.low,
                "v": bar.volume
            } for bar in bars
        ],
        "points": len(bars),
        "mktDataDelay": 0
    }

    return result

def handle_pa_transaction(data):
    return {"status": "received", "transaction": data}

def read_post_data():
    with open('post.json', 'r') as f:
        return json.load(f)

def main():
    if len(sys.argv) < 3:
        print("Usage: python ib_cli.py [GET|POST|DELETE] /path")
        sys.exit(1)

    method = sys.argv[1].upper()
    path = sys.argv[2]
    post_data = read_post_data()
    jsn = processRequest(method, path, post_data)
    print(jsn)

def processRequest(method, path, post_data):
    try:
        line = inspect.currentframe().f_lineno
        result = {"error": f"{line} - handler - processRequest - Failed to process request"}
        if method == "GET":
            if re.match(r"^/iserver/account/[^/]+/summary$", path):
                account_id = path.split('/')[3]
                result = get_account_summary(account_id)
            elif re.match(r"^/portfolio/[^/]+/positions/\d+$", path):
                url = path
                if '?' in url:
                    path, query = url.split('?', 1)
                else:
                    path, query = url, ''

                # Extract accountId and pageId from path
                m = re.match(r'^/portfolio/([^/]+)/positions/(\d+)$', path)
                if not m:
                    raise ValueError(f"URL path format invalid: {path}")
                accountId, pageId = m.group(1), int(m.group(2))

                # Parse query parameters into dict
                params = {}
                if query:
                    for pair in query.split('&'):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            params[k] = v
                        else:
                            params[pair] = ''

                model = params.get('model', None)
                sort = params.get('sort', 'name')
                direction = params.get('direction', 'a')
                waitForSecDef = params.get('waitForSecDef', 'false').lower() == 'true'
                positions = get_positions(accountId, pageId, model, sort, direction, waitForSecDef)
                result = positions
            elif re.match(r"^/iserver/account/orders", path):
                url = path
                if '?' in url:
                    path, query = url.split('?', 1)
                else:
                    path, query = url, ''

                params = {}
                if query:
                    for pair in query.split('&'):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            params[k] = v
                        else:
                            params[pair] = ''

                filters = params.get('filters', [])
                if "," in filters:
                    filters = filters.split(",")
                force = params.get('force', False)
                account_id = params.get('accountId', None)
                result = get_orders(filters, force, account_id)
            elif re.match(r"^/iserver/account/order/status/\d+$", path):
                order_id = extract_order_id(url)
                result = get_order_status(order_id)
                if result:
                    result = result
                else:
                    line = inspect.currentframe().f_lineno
                    result = {"error": f"{line} - handler - processRequest - Order not found"}
            elif re.match(r"^/iserver/secdef/search\?symbol=\w+", path):
                url = path
                if '?' in url:
                    path, query = url.split('?', 1)
                else:
                    path, query = url, ''

                params = {}
                if query:
                    for pair in query.split('&'):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            params[k] = v
                        else:
                            params[pair] = ''
                    result = search(params["symbol"])
                pass
            elif re.match(r"^/iserver/marketdata/history", path):
                url = path
                if '?' in url:
                    path, query = url.split('?', 1)
                else:
                    path, query = url, ''

                params = {}
                if query:
                    for pair in query.split('&'):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            params[k] = v
                        else:
                            params[pair] = ''
                    conid = params["conid"]
                    duration_str = params["period"]
                    bar_size = params["bar"]
                    end_datetime = params["startTime"]
                    result = get_formatted_bars(conid, end_datetime, duration_str, bar_size)
                pass
            elif re.match(r"^/trsrv/secdef", path):
                url = path
                if '?' in url:
                    path, query = url.split('?', 1)
                else:
                    path, query = url, ''

                params = {}
                if query:
                    for pair in query.split('&'):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            params[k] = v
                        else:
                            params[pair] = ''
                conid = params["conids"]
                result = contractLookup(conid)
        elif method == "POST":
            if re.match(r"^/iserver/account/[^/]+/orders$", path):
                account_id = path.split('/')[3]
                jsn = json.loads(post_data)
                result = post_order(account_id, jsn)
            elif path == "/pa/transactions":
                #result = handle_pa_transaction(post_data)
                line = inspect.currentframe().f_lineno
                result = {"error": f"{line} - handler - processRequest - Unsupported method"}
        elif method == "DELETE":
            if re.match(r"^/iserver/account/[^/]+/order/\d+$", path):
                parts = path.split('/')
                result = delete_order(parts[3], int(parts[5]))
        else:
            line = inspect.currentframe().f_lineno
            result = {"error": f"{line} - handler - processRequest - Unsupported method"}
    except Exception as e:
        #print(full_stack())
        line = inspect.currentframe().f_lineno
        result = {"error": f"{line} - handler - processRequest - {e}"}

    return json.dumps(result)

def handle_client(conn, addr):
    try:
        with conn:
            data = ''
            while True:
                chunk = conn.recv(4096).decode("utf-8")
                if not chunk:
                    break
                data += chunk
                if "\n" in chunk:
                    break

            print(f"Message Received: {data}")
            request = json.loads(data.strip())
            action = request.get("action")
            path = request.get("path")
            payload = request.get("data", {})

            response = processRequest(action, path, payload)

            #print(f"Sending response: {response}")
            conn.sendall((response + "\n").encode("utf-8"))
    except Exception as e:
        err = json.dumps({"error": f"handler - handle_client - {e}"})
        conn.sendall((err + "\n").encode("utf-8"))

def start_server():
    global server_socket, threads
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 9009))
    server_socket.listen()

    print("Backend IBKR handler listening on port 9009...")

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        threads.append(thread)
        thread.start()

if __name__ == "__main__":
    # Start the event loop in a dedicated thread
    #th = threading.Thread(target=ib_thread_worker, daemon=True).start()
    #threads.append(th)
    start_server()

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




