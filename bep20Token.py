from web3 import Web3
from abi import bep20TokenAbi

class BEP20Token:

    def __init__(self,tokenAddress,rpcUrl):
        self.web3Connection= Web3(Web3.HTTPProvider(rpcUrl))
        self.tokenAddress = tokenAddress
        self.tokenContract = self.web3Connection.eth.contract(tokenAddress, abi=bep20TokenAbi())

    def getBalanceInWei(self,walletAddress):
        return self.tokenContract.functions.balanceOf(walletAddress).call()
    
    def checkTokenBalanceSufficientWithEther(self,walletAddress,amountInEther):
        balance = self.tokenContract.functions.balanceOf(walletAddress).call()
        if(self.web3Connection.toWei(float(amountInEther),'ether') > balance):
            return False
        else:
            return True