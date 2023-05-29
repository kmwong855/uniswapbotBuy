import datetime
import logging
import os
from os import system
import winsound
import sys
from eth_abi import decode
from decimal import *
import random
from web3 import Web3
from erc20Token import ERC20Token
from BuyTokens import buyTokens
from abi import tokenAbi, erc20TokenAbi
import config as config
import schedule
from decimal import *
from general import *


arb = config.RPC_URL
web3 = Web3(Web3.HTTPProvider(arb))
if web3.is_connected():
    print("Connected to Arbitrum Network")

# Important Addresses
XPEPE_Address = web3.to_checksum_address(config.XPEPE_ADDRESS)
USDT_Address = web3.to_checksum_address(config.USDT_ADDRESS)
USDT_Proxy_Address = web3.to_checksum_address(config.USDT_PROXY_ADDRESS)
sushiswapRouterAddress = web3.to_checksum_address(config.SUSHISWAP_ROUTER_ADDRESS)
walletAddresses = config.YOUR_WALLET_ADDRESS
TradingTokenDecimal = None

# transaction count
tradeCount = 0

# cummulative variables
# Trading volume cap
tradeVolume = config.TOTAL_TRADE_VOLUME
# job, unused change to window task scheduler
tradeCycleJob = {}

totalUsdtSell = 0
totalXpepeBought = 0
totalRejectedAmountBuy = 0
totalEthUsedBuy = 0

UsdtToken = ERC20Token(config.USDT_ADDRESS, arb)
XpepeToken = ERC20Token(config.XPEPE_ADDRESS, arb)

# init logging
now = datetime.datetime.now()
logFileName = "./log/" + now.strftime("%d%m%Y-%H%M-%S")
if os.path.isdir("log"):
    logging.basicConfig(filename=f"{logFileName}.log", level=logging.INFO)
else:
    os.mkdir("log")
    logging.basicConfig(filename=f"{logFileName}.log", level=logging.INFO)


def InitializeTrade():
    global driver
    global TokenToSellAddress
    global TradingTokenDecimal
    # Getting ABI
    BTokenAbi = tokenAbi(XPEPE_Address)

    sushiswapAbi = tokenAbi(sushiswapRouterAddress)

    ATokenAbi = tokenAbi(USDT_Address)

    proxyATokenAbi = tokenAbi(USDT_Proxy_Address)

    # Create a contract for both apeswapRoute and Token to Sell
    contractSushiswap = web3.eth.contract(
        address=sushiswapRouterAddress, abi=sushiswapAbi
    )

    contractAToken = web3.eth.contract(address=USDT_Address, abi=ATokenAbi)
    contractBToken = web3.eth.contract(address=XPEPE_Address, abi=BTokenAbi)

    proxyContractAToken = web3.eth.contract(
        address=config.USDT_PROXY_ADDRESS, abi=proxyATokenAbi
    )

    params = {
        "web3": web3,
        "contractAToken": contractAToken,
        "contractBToken": contractBToken,
        "contractSushiswap": contractSushiswap,
        "sushiswapRouterAddress": sushiswapRouterAddress,
        "XPEPE_Address": XPEPE_Address,
        "USDT_Address": USDT_Address,
        "proxyContractAToken": proxyContractAToken,
    }

    return params


def tradeSummary(params):
    logging.info("----------------------------------------------")
    logging.info(log(f"Trading Summary: "))
    logging.info("----------------------------------------------")

    # usdUsed = 0

    # if afterBNB < initialBNB:
    #     usdDiff = convertBNBToUsdtReturnWei(params, initialBNB - afterBNB) / (10**18)
    #     usdUsed += usdDiff
    #     logging.info(
    #         log(
    #             f"BNB: {afterBNB} BNB ( -{initialBNB - afterBNB} BNB) / ( -{usdDiff} USDT)"
    #         )
    #     )
    # elif afterBNB > initialBNB:
    #     usdDiff = convertBNBToUsdtReturnWei(params, afterBNB - initialBNB) / (10**18)
    #     usdUsed -= usdDiff
    #     logging.info(
    #         log(
    #             f"BNB: {afterBNB} BNB ( +{afterBNB - initialBNB} BNB) / ( +{usdDiff} USDT)"
    #         )
    #     )
    # else:
    #     logging.info(log(f"BNB: {afterBNB} BNB (0)"))

    # if afterCAKE < initialCAKE:
    #     usdDiff = convertArenaToUsdtReturnWei(params, initialCAKE - afterCAKE) / (
    #         10**18
    #     )
    #     usdUsed += usdDiff
    #     logging.info(
    #         log(
    #             f"CAKE: {afterCAKE} CAKE ( -{initialCAKE - afterCAKE} CAKE) / ( -{usdDiff} USDT)"
    #         )
    #     )
    # elif afterCAKE > initialCAKE:
    #     usdDiff = convertArenaToUsdtReturnWei(params, afterCAKE - initialCAKE) / (
    #         10**18
    #     )
    #     usdUsed -= usdDiff
    #     logging.info(
    #         log(
    #             f"CAKE: {afterCAKE} CAKE (+ {afterCAKE - initialCAKE} CAKE) / ( +{usdDiff} USDT)"
    #         )
    #     )
    # else:
    #     logging.info(log(f"CAKE: {afterCAKE} CAKE (0) "))

    # if afterARENA < initialARENA:
    #     usdDiff = convertArenaToUsdtReturnWei(params, initialARENA - afterARENA) / (
    #         10**18
    #     )
    #     usdUsed += usdDiff
    #     logging.info(
    #         log(
    #             f"ARENA: {afterARENA} ARENA ( -{initialARENA - afterARENA} CAKE) / ( -{usdDiff} USDT)"
    #         )
    #     )
    # elif afterARENA > initialARENA:
    #     usdDiff = convertArenaToUsdtReturnWei(params, afterARENA - initialARENA) / (
    #         10**18
    #     )
    #     usdUsed -= usdDiff
    #     logging.info(
    #         log(
    #             f"ARENA: {afterARENA} ARENA ( +{afterARENA - initialARENA} CAKE) / ( +{usdDiff} USDT)"
    #         )
    #     )
    # else:
    #     logging.info(log(f"ARENA: {afterARENA} ARENA (0)"))

    logging.info(log(f"ARENA: {afterARENA} ARENA (0)"))
    # logging.info(log(f"Total USD spent (including gas): {usdUsed} USDT"))
    logging.info("----------------------------------------------")


def generateRandIntFromRange(min, max):
    return random.randint(min, max)


def buyMicroTransaction(
    params, logging, buyTokenAddress, tradeCount, buyVolumeInUSD, buyAddresses, randNum
):
    global totalRejectedAmountBuy, totalEthUsedBuy
    tradeTokenAmount = buyVolumeInUSD
    # tradeTokenAmount = round(
    #     apeswapGetPrice(
    #         params,
    #         [config.USDT_ADDRESS, "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"],
    #         buyVolumeInUSD,
    #         web3,
    #     )
    #     / (10**18),
    #     5,
    # )
    initTradeTokenAmount = tradeTokenAmount

    # logging.info(
    #     log(
    #         f"Trade {tradeCount}: Buy volume is {buyVolumeInUSD} USD -> {round(buyVolumeInUSD,5)} CAKE token"
    #     )
    # )
    boughtTokenAmountCumm = 0

    logging.info(log(f"======================================"))
    logging.info(log(f"Transactions:"))

    # Distribute amount to trade for each wallet
    amountToTrade = randomValues(round(buyVolumeInUSD, 5))

    count = 0
    for wallet in randNum:
        eth = web3.eth.get_balance(buyAddresses[wallet])

        if tradeTokenAmount > 0:
            microTxBuyAmount = amountToTrade[count]

            [buy, boughtTokenAmount] = buyTokens(
                params, microTxBuyAmount, logging, buyAddresses[wallet], wallet
            )

            tradeTokenAmount -= microTxBuyAmount

            # If insufficient USDT
            if buy == 0 and boughtTokenAmount == 0:
                totalRejectedAmountBuy += microTxBuyAmount
                logging.info(
                    log(
                        f" On hold {microTxBuyAmount} USDT, Remaining {round(tradeTokenAmount,5)} USDT to go"
                    )
                )
            else:
                logging.info(log(buy[0]))
                logging.info(
                    log(
                        f" After buy, {microTxBuyAmount} USDT, Remaining {round(tradeTokenAmount,5)} USDT to go"
                    )
                )

            count += 1

            boughtTokenAmountCumm += Decimal(boughtTokenAmount)

            totalEthUsedBuy += round(
                (eth - web3.eth.get_balance(buyAddresses[wallet])) / (10**18), 5
            )
    return initTradeTokenAmount, boughtTokenAmountCumm


def tradeToken(params):
    global tradeCount, tradeVolume

    buyAddresses = config.YOUR_WALLET_ADDRESS
    randNum = randomize()
    if tradeVolume <= 0:
        logging.info(log(f"Trading completed, stop the trade schedule"))
        schedule.cancel_job(tradeCycleJob)
        logging.info(log(f"Cancelled Job, The End"))
        tradeSummary(params)
        # exit script
        sys.exit()
    else:
        logging.info("---------------------------")

        tradeEtherAmountUsd = generateRandIntFromRange(
            config.PER_TRANSACTION_VOLUME_LOWER,
            config.PER_TRANSACTION_VOLUME_UPPER,
        )

        if tradeEtherAmountUsd > tradeVolume and tradeVolume > 0:
            tradeEtherAmountUsd = tradeVolume

        tradeCount += 1

        logging.info(
            log(
                f"Trade {tradeCount}: buy trade volume: {tradeEtherAmountUsd} USDT , current remaining trade volume {tradeVolume-tradeEtherAmountUsd} USDT"
            )
        )

        [spentUSDT, boughtXPEPE] = buyMicroTransaction(
            params,
            logging,
            config.XPEPE_ADDRESS,
            tradeCount,
            tradeEtherAmountUsd,
            buyAddresses,
            randNum,
        )

        global totalUsdtSell, totalXpepeBought

        totalUsdtSell += spentUSDT
        totalXpepeBought += boughtXPEPE

        latestBuyXpepeWithUsdt = boughtXPEPE
        logging.info(
            log(
                f" Trade {tradeCount}: after buy, {round(spentUSDT,5)} USDT for {latestBuyXpepeWithUsdt} XPEPE"
            )
        )
        tradeVolume -= tradeEtherAmountUsd
        return


def grouping():
    totalCountOfAddress = len(walletAddresses)
    totalLoop = 2
    addressGroup = []
    arrAddressess = []
    count = 1

    for arrCount in range(totalCountOfAddress):
        if count == config.ADDRESS_GROUPING:
            arrAddressess.append(walletAddresses[arrCount])
            addressGroup.append(arrAddressess)
            count = 1
            arrAddressess = []
        else:
            arrAddressess.append(walletAddresses[arrCount])
            count += 1

            if arrCount == totalCountOfAddress - 1:
                addressGroup.append(arrAddressess)
                break

    return addressGroup


def randomize():
    walletNum = []
    while len(walletNum) != len(walletAddresses):
        randNum = generateRandIntFromRange(0, config.WALLET_COUNT - 1)
        if randNum not in walletNum:
            walletNum.append(randNum)

    return walletNum


def runCode():
    params = InitializeTrade()

    global tradeCycleJob, totalCakeSell, totalARENABought, totalRejectedAmountBuy, totalBNBUsedBuy

    # not recommended to put below 30s, buy sell have a delay of 5s for transaction verification
    # tradeCycleJob = schedule.every(15).seconds.do(tradeToken, params)
    tradeToken(params)

    # while True:
    #     schedule.run_pending()


if __name__ == "__main__":
    print("starting...")
    # runCode()
    if config.DEBUGGING:
        runCode()
    else:
        try:
            runCode()
        except Exception as Argument:
            # playsound('./error.mp3')
            winsound.PlaySound("beep.wav", winsound.SND_ALIAS)
            logging.info(log(str(Argument)))
