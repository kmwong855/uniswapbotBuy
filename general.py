import config as config
from web3 import Web3
import datetime
import random
from abi import tokenAbi, erc20TokenAbi


def configCheck():
    if (
        config.MICROTRANSACTION_PER_TX_LOWER_PERCENTILE
        > config.MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE
    ):
        raise Exception(
            "Config Error: MICROTRANSACTION_PER_TX_LOWER_PERCENTILE cannot be larger than MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE"
        )
    if (
        config.PER_TRANSACTION_VOLUME_LOWER_USD
        > config.PER_TRANSACTION_VOLUME_UPPER_USD
    ):
        raise Exception(
            "Config Error: PER_TRANSACTION_VOLUME_LOWER_USD cannot be larger than PER_TRANSACTION_VOLUME_UPPER_USD"
        )

    if (
        config.MIN_BUY_MICROTRANSACTION_COUNT < 1
        or config.MAX_BUY_MICROTRANSACTION_COUNT < 1
    ):
        raise Exception(
            "Config Error: BUY_MICROTRANSACTION_COUNT cannot be smaller than 1"
        )
    if (
        config.MIN_SELL_MICROTRANSACTION_COUNT < 1
        or config.MAX_SELL_MICROTRANSACTION_COUNT < 1
    ):
        raise Exception(
            "Config Error: SELL_MICROTRANSACTION_COUNT cannot be smaller than 1"
        )

    if config.MIN_BUY_MICROTRANSACTION_COUNT > config.MAX_BUY_MICROTRANSACTION_COUNT:
        raise Exception(
            "Config Error: MAX_BUY_MICROTRANSACTION_COUNT cannot be larger than MIN_BUY_MICROTRANSACTION_COUNT"
        )
    if config.MIN_SELL_MICROTRANSACTION_COUNT > config.MAX_SELL_MICROTRANSACTION_COUNT:
        raise Exception(
            "Config Error: MIN_SELL_MICROTRANSACTION_COUNT cannot be larger than MAX_SELL_MICROTRANSACTION_COUNT"
        )


def apeswapGetPrice(params, tkArr, swapAmountInEth, webx):
    web3 = Web3(Web3.HTTPProvider(config.RPC_URL_TEST))
    tkArr[1] = web3.to_checksum_address(tkArr[1])
    tkArr[0] = web3.to_checksum_address(tkArr[0])
    if not len(tkArr) == 2:
        raise Exception("invalid array length to check token price")

    if swapAmountInEth <= 0:
        raise Exception("invalid swap amount, cannot be zero")

    tkArrRev = [tkArr[1], tkArr[0]]
    contractApeswap = web3.eth.contract(
        address="0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7",
        abi=tokenAbi(
            web3.to_checksum_address("0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7")
        ),
    )
    contract = contractApeswap
    # contract = params.get("contractApeswap")

    # arena to usd
    amount = web3.to_wei(float(swapAmountInEth), "ether")

    usdtToWBNBinPrice = contract.functions.getAmountsIn(
        amount, [config.WBNB_ADDRESS, tkArr[0]]
    ).call()

    usdtToWBNBoutPrice = contract.functions.getAmountsOut(
        amount,
        [
            tkArr[0],
            config.WBNB_ADDRESS,
        ],
    ).call()

    inPrice = contract.functions.getAmountsIn(
        usdtToWBNBinPrice[0],
        ["0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", config.WBNB_ADDRESS],
    ).call()
    outPrice = contract.functions.getAmountsOut(
        usdtToWBNBoutPrice[1],
        [config.WBNB_ADDRESS, "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"],
    ).call()

    return int((inPrice[0] + outPrice[1]) / 2)


def log(msg):
    logmsg = f"{datetime.datetime.now()} {msg}"
    print(logmsg)
    return logmsg


def randomValues(volume):
    walletLength = len(config.YOUR_WALLET_ADDRESS)
    volumnPerTransaction = volume
    totalSum = 0

    values = [round(random.random(), 5) * 10 for i in range(0, walletLength)]

    s = sum(values)

    values = [round(float((i / s) * volumnPerTransaction), 5) for i in values]

    for x in range(len(values)):
        if x == len(values) - 1:
            values[x] = round(volumnPerTransaction - totalSum, 5)
        else:
            totalSum += values[x]

    return values
