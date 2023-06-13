import config
import time
from erc20Token import ERC20Token
from eth_abi import decode
from general import *
from decimal import *
import math

TokenToBuyAddress = ""
TokenBoughtInEther = 0
tokenDecimal = 0


def buyTokens(kwargs, xpepeBuyAmount, logging, wallet, index):
    global TokenToBuyAddress, tokenDecimal, TokenBoughtInEther

    # log = logging
    web3 = kwargs.get("web3")
    contractRouter = kwargs.get("contractRouter")
    contractRouterAddress = kwargs.get("routerAddress")
    TokenToBuyAddress = kwargs.get("XPEPE_Address")  # XPEPE
    USDT_Address = kwargs.get("USDT_Address")
    UsdtToken = ERC20Token(USDT_Address, config.RPC_URL)
    UsdtTokenContract = kwargs.get("contractAToken")
    proxyContractAToken = kwargs.get("proxyContractAToken")
    toBuyEther = xpepeBuyAmount
    usdtDecimal = kwargs.get("usdt_decimals")
    tokenDecimal = kwargs.get("xpepe_decimals")
    toBuyAmount = web3.to_wei(float(toBuyEther), usdtDecimal)

    # insufficient balance throw exception
    if not UsdtToken.checkTokenBalanceSufficientWithEther(
        wallet, toBuyEther, usdtDecimal
    ):
        walletBalance = round(
            Decimal(UsdtToken.getBalanceInWei(wallet) / web3.to_wei(1, usdtDecimal)), 10
        )
        logging.info(
            log(
                f"(FAILED) {wallet} : Insufficient USDC to trade, need {toBuyEther} to trade but only have {walletBalance}"
            )
        )

        return 0, 0

    # Check allowance
    usdtAllowanceCheck = proxyContractAToken.functions.allowance(
        wallet, contractRouterAddress
    ).call()

    nonceCount = 0

    if usdtAllowanceCheck <= 0:
        max_amount = web3.to_wei(2**64 - 1, "ether")

        tx = proxyContractAToken.functions.approve(
            contractRouterAddress, max_amount
        ).build_transaction(
            {
                "from": wallet,
                "gas": 1600000,
                "gasPrice": web3.to_wei(config.GAS_PRICE_IN_WEI, "gwei"),
                "nonce": web3.eth.get_transaction_count(wallet),
            }
        )

        signed_tx = web3.eth.account.sign_transaction(
            tx, config.YOUR_PRIVATE_KEY[index]
        )

        tx_token = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        nonceCount = 1
        logging.info(log(f"{wallet} : Approve allowance"))

    # swap_txn = contractSushiswap.functions.swapExactTokensForTokens(
    #     toBuyAmount,
    #     1,  # NEED PANCAKE RATE CONVERSION TO BE SAFE
    #     [USDT_Address, TokenToBuyAddress],
    #     wallet,
    # ).build_transaction(
    #     {
    #         "from": wallet,
    #         "gas": 1600000,
    #         "gasPrice": web3.to_wei(config.GAS_PRICE_IN_WEI, "gwei"),
    #         "nonce": web3.eth.get_transaction_count(wallet) + nonceCount,
    #     }
    # )

    payload = (
        USDT_Address,  # tokenIn
        TokenToBuyAddress,  # tokenOut
        10000,  # fee
        wallet,  # recipient
        round(time.time()) + 60 * 20,  # deadline
        toBuyAmount,  # amountIn (exact amount of DAI to be swapped for WETH9)
        0,  # amountOutMinimum
        0,  # sqrtPriceLimitX96
    )

    swap_txn = contractRouter.functions.exactInputSingle(payload).build_transaction(
        {
            "from": wallet,
            "gas": 1600000,
            "gasPrice": web3.to_wei(config.GAS_PRICE_IN_WEI, "gwei"),
            "nonce": web3.eth.get_transaction_count(wallet) + nonceCount,
        }
    )

    signed_txn = web3.eth.account.sign_transaction(
        swap_txn, private_key=config.YOUR_PRIVATE_KEY[index]
    )

    if config.BUY_TOKENS:
        try:
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            # time.sleep(5)
            receipt_success = False
            while not receipt_success:
                try:
                    [TokenBoughtInEther, receipt] = getTokenBought(
                        web3,
                        tx_token,
                    )
                    if receipt.status == 1:
                        receipt_success = True
                except Exception as e:
                    logging.info(log(e))

            result = [
                f"(Success) {wallet} : Bought {TokenBoughtInEther} of PEPEC with {toBuyEther} of USDC token - Transaction Hash:{web3.to_hex(tx_token)}"
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
            print("b")
            return result, None


def getTokenBought(web3, txHash):
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

            tokenBought = Decimal(value[0] / web3.to_wei(1, tokenDecimal))
            break
    return format(tokenBought, ".8f"), tx
