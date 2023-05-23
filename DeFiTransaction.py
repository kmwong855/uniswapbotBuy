# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 15:12:20 2021

@author: Zain
"""
import threading
import time
import datetime
import logging
import os
from os import system
import winsound
import sys
from eth_abi import decode
from decimal import *

# from playsound import playsound
# from pydub import AudioSegment
# from pydub.playback import play

# from bs4 import BeautifulSoup as bsp
# from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.chrome.options import Options
# import winsound
import random

from web3 import Web3

# from webdriver_manager.firefox import GeckoDriverManager
# from webdriver_manager.chrome import ChromeDriverManager
from bep20Token import BEP20Token
from BuyTokens import buyTokens

# from CommandPromptVisuals import changeCmdPosition
from SellTokens import sellTokens
from ThreadingWithReturn import ThreadWithResult
from abi import tokenAbi, bep20TokenAbi

# from sendWhatsappMessage import sendMessage
import config as config
from decimalData import getTokenDecimal

# import schedule
from decimal import *
from general import *

# from apeswapPrice import apeswapPriceQuery

bsc = config.RPC_URL
web3 = Web3(Web3.HTTPProvider(bsc))
if web3.is_connected():
    print("Connected to BSC")

# Important Addresses
arenaAddress = config.ARENA_ADDRESS
TokenToSellAddress = web3.to_checksum_address(arenaAddress)
CAKE_Address = web3.to_checksum_address(config.CAKE_ADDRESS)
apeswapRouterAddress = web3.to_checksum_address(config.APESWAP_ROUTER_ADDRESS)
walletAddresses = config.YOUR_WALLET_ADDRESS
TradingTokenDecimal = None

# transaction count
tradeCount = 0

# cummulative variables
# Trading volume cap
tradeVolume = config.TOTAL_TRADE_VOLUME

# latest bought
latestBuyAreaWithCake = 0
latestSoldArenaForCake = 0


# init logging
now = datetime.datetime.now()
logFileName = "./log/" + now.strftime("%d%m%Y-%H%M-%S")
if os.path.isdir("log"):
    logging.basicConfig(filename=f"{logFileName}.log", level=logging.INFO)
else:
    os.mkdir("log")
    logging.basicConfig(filename=f"{logFileName}.log", level=logging.INFO)

# # job, unused change to window task scheduler
# tradeCycleJob ={}

# variables to keep track of token balance
# initial token balance
initialBNB = 0
initialCAKE = 0
initialARENA = 0

# balance before each trade
startBNB = 0
startCAKE = 0
startARENA = 0

# balance after each trade
afterBNB = 0
afterCAKE = 0
afterARENA = 0

totalCakeSell = 0
totalARENABought = 0
totalRejectedAmountBuy = 0
totalBNBUsedBuy = 0

CakeToken = BEP20Token(config.CAKE_ADDRESS, bsc)
ArenaToken = BEP20Token(config.ARENA_ADDRESS, bsc)


def InitializeTrade():
    global driver
    global TokenToSellAddress
    global TradingTokenDecimal
    # Getting ABI
    sellTokenAbi = tokenAbi(TokenToSellAddress)
    apeswapAbi = tokenAbi(apeswapRouterAddress)
    buyTokenAbi = tokenAbi(CAKE_Address)

    # # Enter you wallet Public Address
    # BNB_balance = web3.eth.get_balance(walletAddress)

    # BNB_balance = web3.from_wei(BNB_balance, 'ether')
    # # print(f"Current BNB Balance: {web3.from_wei(BNB_balance, 'ether')}")

    # Create a contract for both apeswapRoute and Token to Sell
    contractApeswap = web3.eth.contract(address=apeswapRouterAddress, abi=apeswapAbi)

    contractSellToken = web3.eth.contract(TokenToSellAddress, abi=sellTokenAbi)

    contractBuyToken = web3.eth.contract(CAKE_Address, abi=buyTokenAbi)

    if TradingTokenDecimal is None:
        TradingTokenDecimal = contractSellToken.functions.decimals().call()
        TradingTokenDecimal = getTokenDecimal(TradingTokenDecimal)

    # Get current avaliable amount of tokens from the wallet
    # NoOfTokens = contractSellToken.functions.balanceOf(walletAddress).call()
    # NoOfTokens = web3.from_wei(NoOfTokens, TradingTokenDecimal)
    symbol = contractSellToken.functions.symbol().call()

    params = {
        "symbol": symbol,
        "web3": web3,
        "contractBuyToken": contractBuyToken,
        "contractSellToken": contractSellToken,
        "contractApeswap": contractApeswap,
        "apeswapRouterAddress": apeswapRouterAddress,
        "TokenToSellAddress": TokenToSellAddress,
        "CAKE_Address": CAKE_Address,
        "TradingTokenDecimal": TradingTokenDecimal,
    }

    # return BNB_balance, symbol, NoOfTokens, params
    return params


# def startTradeWalletBalanceReport():
#     bnb = web3.eth.get_balance(walletAddress)
#     startBNB = web3.from_wei(bnb, 'ether')
#     startCAKE = CakeToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)
#     startARENA = ArenaToken.getBalanceInWei(
#         config.YOUR_WALLET_ADDRESS)/(10**18)
#     logging.info(log(f'Wallet Balance: '))
#     logging.info(log(f'{startBNB} BNB, {startCAKE} CAKE , {startARENA} ARENA'))
#     return startBNB, startCAKE, startARENA


# def endTradeWalletBalanceReport(startBNB, startCAKE, startARENA):

#     bnb = web3.eth.get_balance(walletAddress)

#     global afterBNB, afterCAKE, afterARENA
#     afterBNB = web3.from_wei(bnb, 'ether')
#     afterCAKE = CakeToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)
#     afterARENA = ArenaToken.getBalanceInWei(
#         config.YOUR_WALLET_ADDRESS)/(10**18)

#     logging.info(log(f'Wallet Balance: '))

#     if (afterBNB < startBNB):
#         logging.info(log(f'BNB: {afterBNB} BNB (- {startBNB - afterBNB})'))
#     elif (afterBNB > startBNB):
#         logging.info(log(f'BNB: {afterBNB} BNB (+ {afterBNB - startBNB})'))
#     else:
#         logging.info(log(f'BNB: {afterBNB} BNB (0)'))

#     if (afterCAKE < startCAKE):
#         logging.info(
#             log(f'CAKE: {afterCAKE} CAKE (- {startCAKE - afterCAKE})'))
#     elif (afterCAKE > startCAKE):
#         logging.info(
#             log(f'CAKE: {afterCAKE} CAKE (+ {afterCAKE - startCAKE})'))
#     else:
#         logging.info(log(f'CAKE: {afterCAKE} CAKE (0)'))

#     if (afterARENA < startARENA):
#         logging.info(
#             log(f'ARENA: {afterARENA} ARENA (- {startARENA - afterARENA})'))
#     elif (afterARENA > startARENA):
#         logging.info(
#             log(f'ARENA: {afterARENA} ARENA (+ {afterARENA - startARENA})'))
#     else:
#         logging.info(log(f'ARENA: {afterARENA} ARENA (0)'))


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


def debuggingModeWaitForSignal(msg):
    if config.DEBUGGING:
        print(msg)
        x = input()


# Micro Transaction functions


def generateRandIntFromRange(min, max):
    return random.randint(min, max)


def buyMicroTransaction(
    params, logging, buyTokenAddress, tradeCount, buyVolumeInUSD, buyAddresses, randNum
):
    global totalRejectedAmountBuy, totalBNBUsedBuy

    tradeTokenAmount = round(
        apeswapGetPrice(
            params,
            [config.USDT_ADDRESS, "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"],
            buyVolumeInUSD,
            web3,
        )
        / (10**18),
        5,
    )
    initTradeTokenAmount = tradeTokenAmount

    logging.info(
        log(
            f"Trade {tradeCount}: Buy volume is {buyVolumeInUSD} USD -> {round(tradeTokenAmount,5)} CAKE token"
        )
    )
    boughtTokenAmountCumm = 0

    logging.info(log(f"======================================"))
    logging.info(log(f"Transactions:"))

    # Distribute amount to trade for each wallet
    amountToTrade = randomValues(round(tradeTokenAmount, 5))

    count = 0
    for wallet in randNum:
        bnb = web3.eth.get_balance(buyAddresses[wallet])

        if tradeTokenAmount > 0:
            microTxBuyAmount = amountToTrade[count]

            [buy, boughtTokenAmount] = buyTokens(
                params, microTxBuyAmount, logging, buyAddresses[wallet], wallet
            )

            tradeTokenAmount -= microTxBuyAmount

            # If insufficient CAKE
            if buy == 0 and boughtTokenAmount == 0:
                totalRejectedAmountBuy += microTxBuyAmount
                logging.info(
                    log(
                        f" On hold {microTxBuyAmount} CAKE, Remaining {round(tradeTokenAmount,5)} CAKE to go"
                    )
                )
            else:
                logging.info(log(buy[0]))
                logging.info(
                    log(
                        f" After buy, {microTxBuyAmount} CAKE for {boughtTokenAmount} ARENA, Remaining {round(tradeTokenAmount,5)} CAKE to go"
                    )
                )

            count += 1

            boughtTokenAmountCumm += Decimal(boughtTokenAmount)

            totalBNBUsedBuy += round(
                (bnb - web3.eth.get_balance(buyAddresses[wallet])) / (10**18), 5
            )
    return initTradeTokenAmount, boughtTokenAmountCumm


def sellMicroTransaction(
    params, logging, sellTokenAddress, tradeCount, sellVolumeInUSD
):
    # how many micro transaction
    microTxCount = generateRandIntFromRange(
        config.MIN_SELL_MICROTRANSACTION_COUNT, config.MAX_SELL_MICROTRANSACTION_COUNT
    )
    tradeTokenAmount = apeswapGetPrice(
        params, [config.USDT_ADDRESS, sellTokenAddress], sellVolumeInUSD
    ) / (10**18)
    initTradeTokenAmount = tradeTokenAmount

    logging.info(
        log(
            f"Trade {tradeCount}: Sell Micro Transaction {microTxCount}, sell volume is {sellVolumeInUSD} USD -> {tradeTokenAmount} ARENA token"
        )
    )
    boughtTokenAmountCumm = 0
    # loop tx
    if not microTxCount == 0 and microTxCount > 1:
        # microTxCount = 2 & above
        for txCount in range(microTxCount):
            if not txCount == (microTxCount - 1):
                percent = generateRandIntFromRange(
                    config.MICROTRANSACTION_PER_TX_LOWER_PERCENTILE,
                    config.MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE,
                )
                microTxSellAmount = round(tradeTokenAmount * percent / 100, 5)
                tradeTokenAmount -= microTxSellAmount
                [sell, boughtTokenAmount] = sellTokens(
                    params, microTxSellAmount, logging
                )
                boughtTokenAmountCumm += boughtTokenAmount
                logging.info(log(sell))
                logging.info(
                    log(
                        f" Trade {tradeCount} mTx {txCount+1}: after sell, {microTxSellAmount} ARENA for {boughtTokenAmount} CAKE, Remaining {tradeTokenAmount} ARENA to go"
                    )
                )
            else:
                [sell, boughtTokenAmount] = sellTokens(
                    params, tradeTokenAmount, logging
                )
                boughtTokenAmountCumm += boughtTokenAmount
                logging.info(log(sell))
                logging.info(
                    log(
                        f" Trade {tradeCount} last mTx {txCount+1}: after sell, {tradeTokenAmount} ARENA for {boughtTokenAmount} CAKE"
                    )
                )
    else:
        # microTxCount = 1 & above
        if microTxCount == 1:
            [buy, boughtTokenAmount] = sellTokens(params, tradeTokenAmount, logging)
            boughtTokenAmountCumm += boughtTokenAmount
            logging.info(log(buy))
            logging.info(
                log(
                    f" Trade {tradeCount} mTx {microTxCount}: after buy, {tradeTokenAmount} ARENA for {boughtTokenAmount} CAKE"
                )
            )
        else:
            logging.info(log(f" Trade {tradeCount} mTx {0}: No Trade for this round"))
            raise Exception("Micro Transaction must have at least 1 transaction")

    return initTradeTokenAmount, boughtTokenAmountCumm


def tradeToken(params):
    global tradeCount, tradeVolume, latestSoldArenaForCake, latestBuyAreaWithCake

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

        # [startBNB, startCAKE, startARENA] = startTradeWalletBalanceReport()

        # generate one time trading volume ( buy & sell volume = trade volume /2 )
        tradeEtherAmountUsd = generateRandIntFromRange(
            config.PER_TRANSACTION_VOLUME_LOWER_USD,
            config.PER_TRANSACTION_VOLUME_UPPER_USD,
        )

        if tradeEtherAmountUsd > tradeVolume and tradeVolume > 0:
            tradeEtherAmountUsd = tradeVolume

        tradeCount += 1
        logging.info(
            log(
                f"Trade {tradeCount}: buy trade volume: {tradeEtherAmountUsd} USD worth of ARENA, current remaining trade volume {tradeVolume-tradeEtherAmountUsd} USD"
            )
        )

        # debuggingModeWaitForSignal('start buy?')

        # [spentCAKE, boughtARENA] = buyMicroTransaction(
        #     params, logging, config.ARENA_ADDRESS, tradeCount, tradeEtherAmountUsd/2, buyAddresses)
        [spentCAKE, boughtARENA] = buyMicroTransaction(
            params,
            logging,
            config.ARENA_ADDRESS,
            tradeCount,
            tradeEtherAmountUsd,
            buyAddresses,
            randNum,
        )
        global totalCakeSell, totalARENABought

        totalCakeSell += spentCAKE
        totalARENABought += boughtARENA

        latestBuyArenaWithCake = boughtARENA
        logging.info(
            log(
                f" Trade {tradeCount}: after buy, {round(spentCAKE,5)} CAKE for {latestBuyArenaWithCake} ARENA"
            )
        )
        tradeVolume -= tradeEtherAmountUsd
        return
        # debuggingModeWaitForSignal('start sell?')
        # logging.info('------')
        # logging.info(log(
        #     f'Trade {tradeCount}: sell trade volume: {tradeEtherAmountUsd/2} USD worth of CAKE, current remaining trade volume {tradeVolume-tradeEtherAmountUsd/2} USD'))
        # [spentARENA, boughtCAKE] = sellMicroTransaction(
        #     params, logging, config.CAKE_ADDRESS, tradeCount, tradeEtherAmountUsd/2)
        # latestSoldArenaForCake = boughtCAKE
        # logging.info(log(
        #     f' Trade {tradeCount}: after sell, {spentARENA} ARENA for {latestSoldArenaForCake} CAKE'))

        # logging.info(log(
        #     f' Trade {tradeCount}: end trade {spentARENA} ARENA, {latestSoldArenaForCake} CAKE'))
        # tradeVolume -= tradeEtherAmountUsd/2

        # returnMsg = f'Trade Cycle: {tradeCount}, Traded {latestBuyArenaWithCake} CAKE & {latestSoldArenaForCake} Arena with {tradeEtherAmountUsd/2} USD, traded volume: {tradeEtherAmountUsd} USD,'
        # remainingTradeMsg = f'left {tradeVolume} USD to go' if not tradeVolume < 0 else f' no remaining volume'
        # logging.info(log(returnMsg + remainingTradeMsg))

        # endTradeWalletBalanceReport(startBNB, startCAKE, startARENA)


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


def test():
    txHash = 0x634D47ED0D14D431FA91133992B8009AE17308E755D028B36D451014BC9D5C04
    TokenToBuyAddress = "0x876563b2510DFFdDAa2c837ab31D78dfE8D42cAd"
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


# def x():
#     walletLength = 5
#     volumnPerTransaction = 1.2
#     totalSum = 0
#     # for x in range(walletLength):

#     #     randNum = generateRandIntFromRange()
#     x = 10

#     values = [round(random.random(), 5) * 10 for i in range(0, walletLength)]

#     s = sum(values)

#     values = [round(float((i / s) * volumnPerTransaction), 5) for i in values]

#     for x in range(len(values)):
#         if x == len(values) - 1:
#             values[x] = round(volumnPerTransaction - totalSum, 5)
#         else:
#             totalSum += values[x]

#     # values[-1] += volumnPerTransaction - sum(values)
#     print(values)
#     print(round(sum(values), 5))
#     return values


def runCode():
    params = InitializeTrade()

    # set initial trade amount usdt to cake
    global latestBuyAreaWithCake, tradeCycleJob, totalCakeSell, totalARENABought, totalRejectedAmountBuy, totalBNBUsedBuy

    # seperate multiple wallets into group

    # groupWalletAddresses = grouping()
    # groupWalletAddresses = config.YOUR_WALLET_ADDRESS
    # randNum = randomize()

    # not recommended to put below 30s, buy sell have a delay of 5s for transaction verification
    # tradeCycleJob = schedule.every(15).seconds.do(tradeToken, params)
    tradeToken(params)

    # bnb = web3.eth.get_balance(walletAddress)

    # global initialBNB, initialCAKE, initialARENA
    # initialBNB = web3.from_wei(bnb, 'ether')
    # initialCAKE = CakeToken.getBalanceInWei(
    #     config.YOUR_WALLET_ADDRESS)/(10**18)
    # initialARENA = ArenaToken.getBalanceInWei(
    #     config.YOUR_WALLET_ADDRESS)/(10**18)
    # configCheck()

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
