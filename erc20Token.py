from web3 import Web3
from abi import erc20TokenAbi


class ERC20Token:
    def __init__(self, tokenAddress, rpcUrl):
        self.web3Connection = Web3(Web3.HTTPProvider(rpcUrl))
        self.tokenAddress = tokenAddress
        self.tokenContract = self.web3Connection.eth.contract(
            tokenAddress, abi=erc20TokenAbi()
        )

    def getBalanceInWei(self, walletAddress):
        return self.tokenContract.functions.balanceOf(walletAddress).call()

    def checkTokenBalanceSufficientWithEther(self, walletAddress, amountInEther):
        balance = self.tokenContract.functions.balanceOf(walletAddress).call()
        if self.web3Connection.to_wei(float(amountInEther), "ether") > balance:
            return False
        else:
            return True
