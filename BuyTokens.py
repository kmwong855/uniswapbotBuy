import config
import time
from bep20Token import BEP20Token
from eth_abi import decode
from general import *
from decimal import *

TokenToBuyAddress = ""
TokenBoughtInEther = 0


def buyTokens(kwargs, arenaBuyAmount, logging, wallet, index):
    # log = logging
    symbol = kwargs.get("symbol")
    web3 = kwargs.get("web3")
    walletAddress = kwargs.get("walletAddress")
    contractApeswap = kwargs.get("contractApeswap")
    contractRouterApeSwap = kwargs.get("apeswapRouterAddress")
    global TokenToBuyAddress
    TokenToBuyAddress = kwargs.get("TokenToSellAddress")  # ARENA
    CAKE_Address = kwargs.get("CAKE_Address")
    CakeToken = BEP20Token(CAKE_Address, config.RPC_URL)
    CakeTokenContract = kwargs.get("contractBuyToken")
    toBuyBNBAmountEther = arenaBuyAmount
    toBuyBNBAmount = web3.to_wei(float(toBuyBNBAmountEther), "ether")

    # TO_DO
    # toBuyBNBAmountMin = int(minArenaExpected*(1-config.SLIPPAGE))
    toBuyBNBAmountMin = 1

    # insufficient balance throw exception
    if not CakeToken.checkTokenBalanceSufficientWithEther(wallet, toBuyBNBAmountEther):
        walletBalance = CakeToken.getBalanceInWei(wallet) / (10**18)
        logging.info(
            log(
                f"(FAILED) {wallet} : Insufficient CAKE to trade, need {toBuyBNBAmountEther} to trade but only have {walletBalance}"
            )
        )

        return 0, 0

    # Check allowance
    cakeAllowanceCheck = CakeTokenContract.functions.allowance(
        wallet, contractRouterApeSwap
    ).call()

    if cakeAllowanceCheck <= 0:
        max_amount = web3.to_wei(2**64 - 1, "ether")

        tx = CakeTokenContract.functions.approve(
            contractRouterApeSwap, max_amount
        ).build_transaction(
            {
                "from": wallet,
                "gasPrice": web3.to_wei(config.GAS_PRICE_IN_WEI, "gwei"),
                "nonce": web3.eth.get_transaction_count(wallet),
            }
        )

        signed_tx = web3.eth.account.sign_transaction(
            tx, config.YOUR_PRIVATE_KEY[index]
        )

        tx_token = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        logging.info(log(f"{wallet} : Approve allowance"))

    apeswap_txn = contractApeswap.functions.swapExactTokensForTokens(
        toBuyBNBAmount,
        1,  # NEED PANCAKE RATE CONVERSION TO BE SAFE
        [CAKE_Address, TokenToBuyAddress],
        wallet,
        (int(time.time() + 10000)),
    ).build_transaction(
        {
            "from": wallet,
            "gas": 1600000,
            "gasPrice": web3.to_wei(config.GAS_PRICE_IN_WEI, "gwei"),
            "nonce": web3.eth.get_transaction_count(wallet),
        }
    )

    signed_txn = web3.eth.account.sign_transaction(
        apeswap_txn, private_key=config.YOUR_PRIVATE_KEY[index]
    )
    global TokenBoughtInEther

    if config.BUY_TOKENS:
        try:
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            # time.sleep(5)
            receipt_success = False
            while not receipt_success:
                try:
                    [TokenBoughtInEther, receipt] = getTokenBought(web3, tx_token)
                    if receipt.status == 1:
                        receipt_success = True
                except Exception as e:
                    logging.info(log(e))

            result = [
                f"(Success) {wallet} : Bought {TokenBoughtInEther} of ARENA  with {web3.from_wei(toBuyBNBAmount, 'ether')} of CAKE token  TransactionHash: {web3.to_hex(tx_token)}"
            ]
            return result, TokenBoughtInEther
        except ValueError as e:
            if e.args[0].get("message") in "intrinsic gas too low":
                result = ["(Failed)", f"ERROR: {e.args[0].get('message')}"], None
            else:
                result = [
                    "(Failed)",
                    f"ERROR: {e.args[0].get('message')} : {e.args[0].get('code')}",
                ]
            raise Exception(result)
    else:
        result = ["Failed", "skip buy tokens, config disabled'"]
        if config.DEBUGGING:
            return result, TokenBoughtInEther  # testing only
        else:
            return result, None


# def getTokenBought(web3, txHash):
#     tokenDecimal = 18
#     tx = web3.eth.wait_for_transaction_receipt(
#         txHash, config.WAIT_FOR_TX_RECEIPT_TIMEMOUT_SECONDS, config.WAIT_FOR_TX_RECEIPT_POLL_FREQUENCY)
#     a = tx.logs
#     tokenBought = 0
#     for log in a:

#         value = decode(['uint256'], bytes.fromhex(log.data[2:]))
#         tokenContractAddress = log.address
#         if (tokenContractAddress == TokenToBuyAddress):  # get the amount of swapped token
#             # shortcut, no token decimal parse from contract
#             tokenBought = value[0] / 10**tokenDecimal
#             break
#     return tokenBought, tx


def getTokenBought(web3, txHash):
    tokenDecimal = 18
    tx = web3.eth.wait_for_transaction_receipt(
        txHash,
        config.WAIT_FOR_TX_RECEIPT_TIMEMOUT_SECONDS,
        config.WAIT_FOR_TX_RECEIPT_POLL_FREQUENCY,
    )
    a = tx.logs

    tokenBought = 0
    for log in a:
        # print(bytes.fromhex(log.data[2:]))
        res = ""
        for b in log.data[2:]:
            res += "%02x" % b

        value = decode(["uint256"], b"\x00" + b"\x00" + bytes.fromhex(res))
        tokenContractAddress = log.address
        if tokenContractAddress == TokenToBuyAddress:  # get the amount of swapped token
            # shortcut, no token decimal parse from contract

            tokenBought = Decimal(value[0] / 10**tokenDecimal)
            break

    return format(tokenBought, ".8f"), tx
