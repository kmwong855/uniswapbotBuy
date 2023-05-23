from web3 import Web3
import config as config
from abi import tokenAbi


class PancakePriceQuery:
    bsc = 'https://bsc-dataseed.binance.org/'
    web3 = {}
    pancakeRouterAddress = ''
    pancakeRoutercontract = {}

    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(self.bsc))
        self.pancakeRouterAddress = self.web3.toChecksumAddress(
            config.APESWAP_ROUTER_ADDRESS)
        self.pancakeContract = self.web3.eth.contract(
            address=self.pancakeRouterAddress, abi=tokenAbi(self.pancakeRouterAddress))

    def checkPricePair(contract, tkArr, swapAmount):
        # asssume tkArr sequence is direct
        if (not len(tkArr) == 2):
            raise Exception('invalid array length to check token price')

        if (swapAmount <= 0):
            raise Exception('invalid swap amount, cannot be zero')

        tkArrRev = tkArr.reverse
        # arena to usd
        inPrice = contract.getAmountsIn(swapAmount, tkArr)
        outPrice = contract.getAmountsOut(swapAmount, tkArrRev)

        return int((inPrice + outPrice) / 2)
