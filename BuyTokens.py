import config
import time
from bep20Token import BEP20Token
from eth_abi import decode

TokenToBuyAddress=''
TokenBoughtInEther=0

def buyTokens(kwargs,arenaBuyAmount,logging):
    log = logging
    symbol = kwargs.get('symbol')
    web3 = kwargs.get('web3')
    walletAddress = kwargs.get('walletAddress')
    contractPancake = kwargs.get('contractPancake')
    global TokenToBuyAddress
    TokenToBuyAddress = kwargs.get('TokenToSellAddress') # ARENA
    CAKE_Address = kwargs.get('CAKE_Address')
    CakeToken = BEP20Token(CAKE_Address,config.RPC_URL)
    toBuyBNBAmountEther = arenaBuyAmount
    toBuyBNBAmount = web3.toWei(float(toBuyBNBAmountEther), 'ether')

    # TO_DO
    # toBuyBNBAmountMin = int(minArenaExpected*(1-config.SLIPPAGE))
    toBuyBNBAmountMin = 1

    # insufficient balance throw exception
    if(not CakeToken.checkTokenBalanceSufficientWithEther(config.YOUR_WALLET_ADDRESS,toBuyBNBAmountEther)):
        walletBalance = CakeToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)
        raise Exception(f'Need {toBuyBNBAmountEther} CAKE to trade, but you only have {walletBalance} CAKE')
   
    pancakeSwap_txn = contractPancake.functions.swapExactTokensForTokens(
        toBuyBNBAmount,
        toBuyBNBAmountMin, # NEED PANCAKE RATE CONVERSION TO BE SAFE
        [CAKE_Address, TokenToBuyAddress],
        walletAddress,
        (int(time.time() + 10000))).buildTransaction({
        'from': walletAddress,
        'gas': 160000,
        'gasPrice': web3.toWei(config.GAS_PRICE_IN_WEI, 'gwei'),
        'nonce': web3.eth.get_transaction_count(walletAddress)
    })

    signed_txn = web3.eth.account.sign_transaction(pancakeSwap_txn, private_key=config.YOUR_PRIVATE_KEY)
    global TokenBoughtInEther

    # for testing
    if(config.DEBUGGING):
        [TokenBoughtInEther,receipt] = getTokenBought(web3,"0xd48e5224bfb69782a8069a77a4aee219bc0aa8fdba0abb002e1b83ac97645503") # testing only

    if config.BUY_TOKENS:
        try:
            if(config.DEBUGGING):
                print('continue to buy? no just quit')
                x = input()

            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            # time.sleep(5)
            receipt_success= False
            while(not receipt_success):
                try:
                    [TokenBoughtInEther,receipt] = getTokenBought(web3,tx_token)
                    if(receipt.status ==1):
                        receipt_success = True
                except Exception as e:
                    log.info(e)
                    print(e)

            result = [web3.toHex(tx_token), f"Bought {TokenBoughtInEther} of ARENA  with {web3.fromWei(toBuyBNBAmount, 'ether')} of CAKE token  TransactionHash: {web3.toHex(tx_token)}"]
            return result,TokenBoughtInEther
        except ValueError as e:
            if e.args[0].get('message') in 'intrinsic gas too low':
                result = ["Failed", f"ERROR: {e.args[0].get('message')}"],None
            else:
                result = ["Failed", f"ERROR: {e.args[0].get('message')} : {e.args[0].get('code')}"]
            raise Exception(result)
            return result,None
    else:
        result = ["Failed", "skip buy tokens, config disabled'"]
        if(config.DEBUGGING):
            return result,TokenBoughtInEther # testing only
        else:
            return result,None

def getTokenBought(web3,txHash):
    tokenDecimal = 18
    tx = web3.eth.wait_for_transaction_receipt(txHash,config.WAIT_FOR_TX_RECEIPT_TIMEMOUT_SECONDS,config.WAIT_FOR_TX_RECEIPT_POLL_FREQUENCY)
    a = tx.logs
    tokenBought =0
    for log in a:
        value = decode(['uint256'], bytes.fromhex(log.data[2:]))
        tokenContractAddress = log.address
        if(tokenContractAddress == TokenToBuyAddress): #get the amount of swapped token
           tokenBought = value[0] / 10**tokenDecimal # shortcut, no token decimal parse from contract
           break
    return tokenBought,tx