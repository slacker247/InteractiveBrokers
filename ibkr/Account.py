'''
'accountType': '', 'status': '', 'balance': 28681.0, 'SMA': 28707.0, 'buyingPower': 114725.0, 'availableFunds': 28681.0,
 'excessLiquidity': 28681.0, 'netLiquidationValue': 28687.0, 'equityWithLoanValue': 28681.0, 
 'regTLoan': 0.0, 'securitiesGVP': 0.0, 'totalCashValue': 28681.0, 'accruedInterest': 0.0, 
 'regTMargin': 0.0, 'initialMargin': 0.0, 'maintenanceMargin': 0.0,
   'cashBalances': [{'currency': 'USD', 'balance': 28681.0, 'settledCash': 28681.0}]
'''
class Account:
    def __init__(self):
        self.id = ""
        self.accountcode = ""
        self.accountType = ""
        self.status = ""
        self.balance = 0.0
        self.SMA = 0.0
        self.buyingPower = 0.0
        self.availableFunds = 0.0
        self.excessLiquidity = 0.0
        self.netLiquidationValue = 0.0
        self.equityWithLoanValue = 0.0
        self.regTLoan = 0.0
        self.securitiesGVP = 0.0
        self.totalCashValue = 0.0
        self.accruedInterest = 0.0
        self.regTMargin = 0.0
        self.initialMargin = 0.0
        self.maintenanceMargin = 0.0

        self.PrepaidCrypto_Z = False
        self.PrepaidCrypto_P = False
        self.brokerageAccess = True
        self.accountId = ""
        self.accountVan = ""
        self.accountTitle =""
        self.displayName = ""
        self.accountAlias = None
        self.accountStatus = 0
        self.currency = "USD"
        self.type = "DEMO"
        self.tradingType = ""
        self.businessType = ""
        self.ibEntity = ""
        self.faclient = False
        self.clearingStatus = ""
        self.covestor = False
        self.noClientTrading = False
        self.trackVirtualFXPortfolio = True
        self.acctCustType = ""
        #self.parent = {
        #    "mmc": [],
        #    "accountId": "",
        #    "isMParent": False,
        #    "isMChild": False,
        #    "isMultiplex": False
        #    },
        self.desc = ""
        
    def setId(self, id):
        self.id = id
        self.accountcode = id

    def to_dict(self):
        return self.__dict__
    
















