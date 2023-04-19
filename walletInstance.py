from web3 import Web3

class WalletInstance:

    def __init__(self,walletAddress,rpcUrl):
        self.web3Connection= Web3(Web3.HTTPProvider(rpcUrl))
        self.walletAddress = walletAddress
        self.BNBbalance = web3.eth.get_balance(walletAddress)

    def getWalletBalance(self,inWei):
        balance = self.web3Connection.eth.get_balance(self.walletAddress)
        if(inWei):
            return balance
        else:
            return balance/(10**18)
