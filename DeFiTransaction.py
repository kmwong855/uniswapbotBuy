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
from decimalData import getTokenDecimal

arb = config.RPC_URL
web3 = Web3(Web3.HTTPProvider(arb))
if web3.is_connected():
    print("Connected to Arbitrum Network")

# Important Addresses
XPEPE_Address = web3.to_checksum_address(config.XPEPE_ADDRESS)
# XPEPE_Proxy_Address = web3.to_checksum_address(config.XPEPE_PROXY_ADDRESS)
USDT_Address = web3.to_checksum_address(config.USDT_ADDRESS)
USDT_Proxy_Address = web3.to_checksum_address(config.USDT_PROXY_ADDRESS)
routerAddress = web3.to_checksum_address(config.ROUTER_ADDRESS)
walletAddresses = config.YOUR_WALLET_ADDRESS
TradingTokenDecimal = None

# transaction count
tradeCount = 0

# cummulative variables
# Trading volume cap
# tradeVolume = config.TOTAL_TRADE_VOLUME
tradeVolume = 0.0002
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
    global TradingTokenDecimal
    # Getting ABI

    routerAbi = tokenAbi(routerAddress)

    ATokenAbi = tokenAbi(USDT_Address)
    BTokenAbi = tokenAbi(XPEPE_Address)

    proxyATokenAbi = tokenAbi(USDT_Proxy_Address)
    # proxyBTokenAbi = tokenAbi(XPEPE_Proxy_Address)

    # Create a contract for both apeswapRoute and Token to Sell
    contractRouter = web3.eth.contract(address=routerAddress, abi=routerAbi)

    contractAToken = web3.eth.contract(address=USDT_Address, abi=ATokenAbi)
    contractBToken = web3.eth.contract(address=XPEPE_Address, abi=BTokenAbi)

    proxyContractAToken = web3.eth.contract(address=USDT_Address, abi=proxyATokenAbi)
    # proxyContractBToken = web3.eth.contract(address=XPEPE_Address, abi=proxyBTokenAbi)
    proxyContractBToken = contractBToken

    # Get USDT Decimal
    TradingTokenADecimal = proxyContractAToken.functions.decimals().call()
    TradingTokenADecimal = getTokenDecimal(TradingTokenADecimal)

    TradingTokenBDecimal = proxyContractBToken.functions.decimals().call()
    TradingTokenBDecimal = getTokenDecimal(TradingTokenBDecimal)

    params = {
        "web3": web3,
        "contractAToken": contractAToken,
        "contractBToken": contractBToken,
        "contractRouter": contractRouter,
        "routerAddress": routerAddress,
        "XPEPE_Address": XPEPE_Address,
        "USDT_Address": USDT_Address,
        "proxyContractAToken": proxyContractAToken,
        "usdt_decimals": TradingTokenADecimal,
        "xpepe_decimals": TradingTokenBDecimal,
    }

    return params


def tradeSummary():
    logging.info("----------------------------------------------")
    logging.info(log(f"Trading Summary: "))
    logging.info("----------------------------------------------")
    logging.info(log(f"USDC Token used : {totalUsdtSell}"))
    logging.info(log(f"PEPEC Token Bought : {totalXpepeBought}"))
    logging.info(log(f"Eth Token used : {totalEthUsedBuy}"))
    logging.info(log(f"Total volume USDT onhold (failed) : {totalRejectedAmountBuy}"))
    logging.info("----------------------------------------------")


def generateRandIntFromRange(min, max):
    return random.randint(min, max)


def buyMicroTransaction(
    params, logging, buyTokenAddress, tradeCount, buyVolumeInUSD, buyAddresses, randNum
):
    global totalRejectedAmountBuy, totalEthUsedBuy
    tradeTokenAmount = buyVolumeInUSD

    initTradeTokenAmount = tradeTokenAmount

    boughtTokenAmountCumm = 0

    logging.info(log(f"======================================"))
    logging.info(log(f"Transactions:"))

    # Distribute amount to trade for each wallet
    amountToTrade = randomValues(round(tradeTokenAmount, 5))

    count = 0
    for wallet in randNum:
        eth = web3.eth.get_balance(buyAddresses[wallet])

        if tradeTokenAmount > 0:
            microTxBuyAmount = amountToTrade[count]

            [buy, boughtTokenAmount] = buyTokens(
                params, microTxBuyAmount, logging, buyAddresses[wallet], wallet
            )

            tradeTokenAmount = Decimal(tradeTokenAmount) - Decimal(microTxBuyAmount)

            # If insufficient USDT
            if buy == 0 and boughtTokenAmount == 0:
                totalRejectedAmountBuy = round(
                    totalRejectedAmountBuy + microTxBuyAmount, 5
                )

                logging.info(
                    log(
                        f" On hold {microTxBuyAmount} USDC, Remaining {round(abs(tradeTokenAmount),5)} USDC to go"
                    )
                )
            else:
                logging.info(log(buy[0]))
                logging.info(
                    log(
                        f" After buy, {microTxBuyAmount} USDC, Remaining {round(abs(tradeTokenAmount),5)} USDC to go"
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
        tradeSummary()
        # exit script
        sys.exit()
    else:
        logging.info("---------------------------")

        # tradeEtherAmountUsd = generateRandIntFromRange(
        #     config.PER_TRANSACTION_VOLUME_LOWER,
        #     config.PER_TRANSACTION_VOLUME_UPPER,
        # )
        tradeEtherAmountUsd = 0.0001

        if tradeEtherAmountUsd > tradeVolume and tradeVolume > 0:
            tradeEtherAmountUsd = tradeVolume

        tradeCount += 1

        logging.info(
            log(
                f"Trade {tradeCount}: buy trade volume: {tradeEtherAmountUsd} USDC , current remaining trade volume {round(tradeVolume-tradeEtherAmountUsd,5)} USDC"
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
                f" Trade {tradeCount}: after buy, {round(spentUSDT,5)} USDC for {latestBuyXpepeWithUsdt} PEPEC"
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
    global tradeCycleJob

    # not recommended to put below 30s, buy sell have a delay of 5s for transaction verification
    tradeCycleJob = schedule.every(15).seconds.do(tradeToken, params)
    # tradeToken(params)

    while True:
        schedule.run_pending()


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
