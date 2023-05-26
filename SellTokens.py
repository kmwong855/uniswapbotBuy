import time
import config
from erc20Token import ERC20Token
from eth_abi import decode

TokenSoldForAddress = ""
TokenSoldForUSDInEther = 0


def sellTokens(kwargs, arenaSellAmount, logging):
    log = logging
    symbol = kwargs.get("symbol")
    web3 = kwargs.get("web3")
    walletAddress = kwargs.get("walletAddress")
    contractPancake = kwargs.get("contractPancake")
    pancakeRouterAddress = kwargs.get("pancakeRouterAddress")
    TokenToSellAddress = kwargs.get("TokenToSellAddress")
    TokenToSellContract = ERC20Token(TokenToSellAddress, config.RPC_URL)
    tokensToSellEther = float(arenaSellAmount)
    CAKE_Address = kwargs.get("CAKE_Address")
    global TokenSoldForAddress
    TokenSoldForAddress = CAKE_Address
    contractSellToken = kwargs.get("contractSellToken")
    TradingTokenDecimal = kwargs.get("TradingTokenDecimal")

    tokenToSell = web3.toWei(tokensToSellEther, TradingTokenDecimal)

    # TO_DO
    # tokenToSellMin = int(minCakeExpected*(1-config.SLIPPAGE))
    tokenToSellMin = 1

    # insufficient balance throw exception
    if not TokenToSellContract.checkTokenBalanceSufficientWithEther(
        config.YOUR_WALLET_ADDRESS, tokensToSellEther
    ):
        walletBalance = TokenToSellContract.getBalanceInWei(
            config.YOUR_WALLET_ADDRESS
        ) / (10**18)
        raise Exception(
            f"Need {tokensToSellEther} CAKE to trade, but you only have {walletBalance} CAKE"
        )

    symbol = contractSellToken.functions.symbol().call()

    pancakeSwap_txn = contractPancake.functions.swapExactTokensForTokens(
        tokenToSell,
        tokenToSellMin,
        [TokenToSellAddress, CAKE_Address],
        walletAddress,
        (int(time.time() + 10000)),
    ).buildTransaction(
        {
            "from": walletAddress,
            "gas": 160000,
            "gasPrice": web3.toWei(config.GAS_PRICE_IN_WEI, "gwei"),
            "nonce": web3.eth.get_transaction_count(walletAddress),
        }
    )

    signed_txn = web3.eth.account.sign_transaction(
        pancakeSwap_txn, private_key=config.YOUR_PRIVATE_KEY
    )

    global TokenSoldForUSDInEther
    # for testing
    if config.DEBUGGING:
        [TokenSoldForUSDInEther, receipt] = getTokenBought(
            web3, "0x8264218ccc46f2d5be3f5d83d7d1a192ef69eadeb7943e54cc75f9d24d917ff2"
        )  # testing only

    if config.SELL_TOKENS:
        try:
            if config.DEBUGGING:
                print("continue to sell? no just quit")
                x = input()
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            # time.sleep(5)
            receipt_success = False
            while not receipt_success:
                try:
                    [TokenSoldForUSDInEther, receipt] = getTokenBought(web3, tx_token)
                    if receipt.status == 1:
                        receipt_success = True
                except Exception as e:
                    log.info(e)
                    print(e)  # need logging

            result = [
                web3.toHex(tx_token),
                f"Sold {web3.fromWei(tokenToSell, TradingTokenDecimal)} {symbol} for {TokenSoldForUSDInEther} CAKE  TransactionHash: {web3.toHex(tx_token)}",
            ]
            return result, TokenSoldForUSDInEther
        except ValueError as e:
            if e.args[0].get("message") in "intrinsic gas too low":
                result = ["Failed", f"ERROR: {e.args[0].get('message')}"]
            else:
                result = [
                    "Failed",
                    f"ERROR: {e.args[0].get('message')} : {e.args[0].get('code')}",
                ]
            raise Exception(result)
            return result, None
    else:
        result = ["Failed", "skip sell tokens, config disabled'"]
        if config.DEBUGGING:
            return result, TokenSoldForUSDInEther  # testing only
        else:
            return result, None


def getTokenBought(web3, txHash):
    tokenDecimal = 18
    tx = web3.eth.wait_for_transaction_receipt(
        txHash,
        config.WAIT_FOR_TX_RECEIPT_TIMEMOUT_SECONDS,
        config.WAIT_FOR_TX_RECEIPT_POLL_FREQUENCY,
    )
    a = tx.logs
    tokenSoldFor = 0
    for log in a:
        value = decode(["uint256"], bytes.fromhex(log.data[2:]))
        tokenContractAddress = log.address

        if (
            tokenContractAddress == TokenSoldForAddress
        ):  # get the amount of swapped token
            tokenSoldFor = (
                value[0] / 10**tokenDecimal
            )  # shortcut, no token decimal parse from contract
            break
    return tokenSoldFor, tx
