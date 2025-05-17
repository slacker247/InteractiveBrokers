
class Position:
    def __init__(self):
        self.acctId = ""
        self.conid = -1
        self.contractDesc = ""
        self.position = 0.0
        self.mktPrice = 0.0
        self.mktValue = 0.0
        self.currency = ""
        self.avgCost = 0.0
        self.avgPrice = 0.0
        self.realizedPnl = 0
        self.unrealizedPnl = 0.0
        self.exchs = None
        self.expiry = None
        self.putOrCall = None
        self.multiplier = 0
        self.strike = "0"
        self.exerciseStyle = None
        self.conExchMap = []
        self.assetClass = ""
        self.undConid = 0
        self.model = ""
        #"incrementRules": [
        #    {
        #        "lowerEdge": 0,
        #        "increment": 0.25
        #    }
        #],
        #"displayRule": {
        #    "magnification": 0,
        #    "displayRuleStep": [
        #        {
        #        "decimalDigits": 2,
        #        "lowerEdge": 0,
        #        "wholeDigits": 4
        #        }
        #    ]
        #},
        self.time = 0
        self.chineseName = ""
        self.allExchanges = ""
        self.listingExchange = ""
        self.countryCode = ""
        self.name = ""
        self.lastTradingDay = None
        self.group = None
        self.sector = None
        self.sectorGroup = None
        self.ticker = ""
        self.type = ""
        self.hasOptions = False
        self.fullName = ""
        self.isEventContract = False
        self.pageSize = 0

    def to_dict(self):
        return self.__dict__

