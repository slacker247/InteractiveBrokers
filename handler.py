import socket
import sys
from datetime import datetime
import json
import re
# https://ib-insync.readthedocs.io/api.html
from ib_insync import *


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

def connect_ib():
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)
    return ib

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
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)

    summary = ib.accountSummary()
    parsed = parse_account_summary(summary)

    ib.disconnect()
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
    ib = connect_ib()

    # Request positions (note: ib.positions() returns a list of (contract, position, avgCost) tuples)
    # positions() does not filter by account, so filter here.
    all_positions = ib.positions()

    # Filter by accountId
    positions_filtered = [
        (contract, pos, avgCost) for (account, contract, pos, avgCost) in all_positions if account == accountId
    ]

    # If waitForSecDef is True, fetch security definitions for all contracts
    if waitForSecDef:
        for contract, _, _ in positions_filtered:
            ib.reqContractDetails(contract)

    # Convert positions to output dicts like your format
    result = []
    for contract, position, avgCost in positions_filtered:
        # Get market price
        ticker = ib.reqMktData(contract, "", False, False)
        ib.sleep(0.1)  # brief wait to get market data

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
    ib.disconnect()
    return result[start:end]

def post_order(account_id, orders_data):
    ib = connect_ib()

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
        ib.qualifyContracts(contract)
        trade = ib.placeOrder(contract, order)
        ib.sleep(1)  # give time for order to register

        results.append({
            "order_id": str(trade.order.orderId),
            "order_status": trade.orderStatus.status,
            "encrypt_message": "1"  # Mocked for format compatibility
        })

    ib.disconnect()
    return results

def delete_order(account_id, order_id):
    ib = connect_ib()
    # Try to cancel the order
    try:
        orders = ib.reqOpenOrders()
        order_found = None
        for t in orders:
            if t.order.orderId == order_id:
                order_found = t

        if order_found:
            ib.cancelOrder(order_found.order)
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
    finally:
        ib.disconnect()

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
    ib = connect_ib()

    if force:
        ib.reqGlobalCancel()

    ib.sleep(0.5)  # Let it clear

    open_orders = ib.reqOpenOrders()
    ib.sleep(0.5)
    trades = ib.trades()

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

    ib.disconnect()
    return {
        "orders": formatted,
        "snapshot": True
    }

def extract_order_id(url):
    match = re.match(r'^GET\s+/v1/api/iserver/account/order/status/(\d+)$', url)
    if not match:
        print("Invalid URL format. Expected: GET /v1/api/iserver/account/order/status/{orderId}")
        sys.exit(1)
    return int(match.group(1))

def get_order_status(order_id):
    ib = connect_ib()
    trades = ib.trades()
    ib.disconnect()
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

    try:
        result = None
        if method == "GET":
            if re.match(r"^/v1/api/iserver/account/[^/]+/summary$", path):
                account_id = path.split('/')[5]
                result = get_account_summary(account_id)
            elif re.match(r"^/v1/api/portfolio/[^/]+/positions/\d+$", path):
                url = path
                if '?' in url:
                    path, query = url.split('?', 1)
                else:
                    path, query = url, ''

                # Extract accountId and pageId from path
                m = re.match(r'^/v1/api/portfolio/([^/]+)/positions/(\d+)$', path)
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
            elif re.match(r"^/v1/api/iserver/account/orders", path):
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
            elif re.match(r"^/v1/api/iserver/account/order/status/\d+$", path):
                order_id = extract_order_id(url)
                result = get_order_status(order_id)
                if result:
                    result = result
                else:
                    result = {"error": "Order not found"}
        elif method == "POST":
            post_data = read_post_data()
            if re.match(r"^/v1/api/iserver/account/[^/]+/orders$", path):
                account_id = path.split('/')[5]
                result = post_order(account_id, post_data)
            elif path == "/pa/transactions":
                #result = handle_pa_transaction(post_data)
                result = {"error": "Unsupported method"}
        elif method == "DELETE":
            if re.match(r"^/v1/api/iserver/account/[^/]+/order/\d+$", path):
                parts = path.split('/')
                result = delete_order(parts[5], int(parts[7]))
        else:
            result = {"error": "Unsupported method"}
    except Exception as e:
        #print(full_stack())
        result = {"error": str(e)}

    print(json.dumps(result))

if __name__ == "__main__":
    main()

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

'''
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



