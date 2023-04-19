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
from abi import tokenAbi,bep20TokenAbi
# from sendWhatsappMessage import sendMessage
import config as config
from decimalData import getTokenDecimal
import schedule
from decimal import *

# from pancakePrice import PancakePriceQuery

bsc = config.RPC_URL
web3 = Web3(Web3.HTTPProvider(bsc))
if web3.isConnected(): print("Connected to BSC")

# User Input Address for Token
if bool(config.ARENA_ADDRESS):
    address = config.ARENA_ADDRESS
else:
    address = input('Enter token address: ')

# Important Addresses
TokenToSellAddress = web3.toChecksumAddress(address)
CAKE_Address = web3.toChecksumAddress(config.CAKE_ADDRESS)
pancakeRouterAddress = web3.toChecksumAddress(config.PANCAKE_ROUTER_ADDRESS)
walletAddress = config.YOUR_WALLET_ADDRESS
TradingTokenDecimal = None

# transaction count
tradeCount = 0

#cummulative variables
# Trading volume cap
tradeVolume = config.TOTAL_TRADE_VOLUME

# latest bought
latestBuyAreaWithCake = 0
latestSoldArenaForCake = 0

# init logging
now = datetime.datetime.now()
logFileName = './log/'+now.strftime('%d%m%Y-%H%M-%S')
if(os.path.isdir('log')):
    logging.basicConfig(filename=f"{logFileName}.log", level=logging.INFO)
else:
    os.mkdir('log')
    logging.basicConfig(filename=f"{logFileName}.log", level=logging.INFO)

# # job, unused change to window task scheduler
# tradeCycleJob ={}

# variables to keep track of token balance
# initial token balance
initialBNB=0
initialCAKE=0
initialARENA=0

#balance before each trade
startBNB=0
startCAKE=0
startARENA=0

#balance after each trade
afterBNB=0
afterCAKE=0
afterARENA=0

CakeToken = BEP20Token(config.CAKE_ADDRESS,bsc)
ArenaToken = BEP20Token(config.ARENA_ADDRESS,bsc)

def configCheck():
    if(config.MICROTRANSACTION_PER_TX_LOWER_PERCENTILE > config.MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE):
        raise Exception('Config Error: MICROTRANSACTION_PER_TX_LOWER_PERCENTILE cannot be larger than MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE')
    if(config.PER_TRANSACTION_VOLUME_LOWER_USD > config.PER_TRANSACTION_VOLUME_UPPER_USD):
        raise Exception('Config Error: PER_TRANSACTION_VOLUME_LOWER_USD cannot be larger than PER_TRANSACTION_VOLUME_UPPER_USD')
    
    if(config.MIN_BUY_MICROTRANSACTION_COUNT < 1 or config.MAX_BUY_MICROTRANSACTION_COUNT < 1):
        raise Exception('Config Error: BUY_MICROTRANSACTION_COUNT cannot be smaller than 1')
    if(config.MIN_SELL_MICROTRANSACTION_COUNT < 1 or config.MAX_SELL_MICROTRANSACTION_COUNT < 1):
        raise Exception('Config Error: SELL_MICROTRANSACTION_COUNT cannot be smaller than 1')
    
    if(config.MIN_BUY_MICROTRANSACTION_COUNT > config.MAX_BUY_MICROTRANSACTION_COUNT):
        raise Exception('Config Error: MAX_BUY_MICROTRANSACTION_COUNT cannot be larger than MIN_BUY_MICROTRANSACTION_COUNT')
    if(config.MIN_SELL_MICROTRANSACTION_COUNT > config.MAX_SELL_MICROTRANSACTION_COUNT):
        raise Exception('Config Error: MIN_SELL_MICROTRANSACTION_COUNT cannot be larger than MAX_SELL_MICROTRANSACTION_COUNT')

def InitializeTrade():
    global driver
    global TokenToSellAddress
    global TradingTokenDecimal
    # Getting ABI
    sellTokenAbi = tokenAbi(TokenToSellAddress)
    pancakeAbi = tokenAbi(pancakeRouterAddress)

    # Enter you wallet Public Address
    BNB_balance = web3.eth.get_balance(walletAddress)
    BNB_balance = web3.fromWei(BNB_balance, 'ether')
    # print(f"Current BNB Balance: {web3.fromWei(BNB_balance, 'ether')}")

    # Create a contract for both PancakeRoute and Token to Sell
    contractPancake = web3.eth.contract(address=pancakeRouterAddress, abi=pancakeAbi)

    contractSellToken = web3.eth.contract(TokenToSellAddress, abi=sellTokenAbi)
    if TradingTokenDecimal is None:
        TradingTokenDecimal = contractSellToken.functions.decimals().call()
        TradingTokenDecimal = getTokenDecimal(TradingTokenDecimal)

    # Get current avaliable amount of tokens from the wallet
    NoOfTokens = contractSellToken.functions.balanceOf(walletAddress).call()
    NoOfTokens = web3.fromWei(NoOfTokens, TradingTokenDecimal)
    symbol = contractSellToken.functions.symbol().call()



    params = {
        'symbol': symbol,
        'web3': web3,
        'walletAddress': walletAddress,
        'contractSellToken': contractSellToken,
        'contractPancake': contractPancake,
        'pancakeRouterAddress': pancakeRouterAddress,
        'TokenToSellAddress': TokenToSellAddress,
        'CAKE_Address': CAKE_Address,
        'TradingTokenDecimal': TradingTokenDecimal,
    }
    return BNB_balance, symbol, NoOfTokens, params

def log(msg):
    logmsg =f'{datetime.datetime.now()} {msg}'
    print(logmsg)
    return logmsg

def pancakeGetPrice(params,tkArr,swapAmountInEth):
    if( not len(tkArr) == 2):
        raise Exception('invalid array length to check token price')

    if(swapAmountInEth <= 0):
        raise Exception('invalid swap amount, cannot be zero')

    tkArrRev = [tkArr[1],tkArr[0]]
    contract = params.get('contractPancake')

    #arena to usd
    amount = web3.toWei(float(swapAmountInEth), 'ether')

    inPrice = contract.functions.getAmountsIn(amount,tkArr).call()
    outPrice = contract.functions.getAmountsOut(amount,tkArrRev).call()
    return int((inPrice[0] + outPrice[1]) / 2)

def convertUsdtToCakeReturnWei(params,amount):
    return pancakeGetPrice(params,["0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82","0x55d398326f99059fF775485246999027B3197955"],amount)

def convertCakeToUsdtReturnWei(params,amount):
    return pancakeGetPrice(params,["0x55d398326f99059fF775485246999027B3197955","0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"],amount)

def convertArenaToUsdtReturnWei(params,amount):
    return pancakeGetPrice(params,["0x55d398326f99059fF775485246999027B3197955","0xCfFD4D3B517b77BE32C76DA768634dE6C738889B"],amount)

def convertBNBToUsdtReturnWei(params,amount):
    return pancakeGetPrice(params,["0x55d398326f99059fF775485246999027B3197955","0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"],amount)

def startTradeWalletBalanceReport():
    bnb = web3.eth.get_balance(walletAddress)
    startBNB = web3.fromWei(bnb, 'ether')
    startCAKE = CakeToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)
    startARENA = ArenaToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)
    logging.info(log(f'Wallet Balance: '))
    logging.info(log(f'{startBNB} BNB, {startCAKE} CAKE , {startARENA} ARENA'))
    return startBNB,startCAKE,startARENA

def endTradeWalletBalanceReport(startBNB,startCAKE,startARENA):

    bnb = web3.eth.get_balance(walletAddress)

    global afterBNB, afterCAKE,afterARENA
    afterBNB = web3.fromWei(bnb, 'ether')
    afterCAKE = CakeToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)
    afterARENA = ArenaToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)

    logging.info(log(f'Wallet Balance: '))
    
    if(afterBNB < startBNB):
        logging.info(log(f'BNB: {afterBNB} BNB (- {startBNB - afterBNB})'))
    elif(afterBNB > startBNB):
        logging.info(log(f'BNB: {afterBNB} BNB (+ {afterBNB - startBNB})'))
    else:
        logging.info(log(f'BNB: {afterBNB} BNB (0)'))

    if(afterCAKE < startCAKE):
        logging.info(log(f'CAKE: {afterCAKE} CAKE (- {startCAKE - afterCAKE})'))
    elif(afterCAKE > startCAKE):
        logging.info(log(f'CAKE: {afterCAKE} CAKE (+ {afterCAKE - startCAKE})'))
    else:
        logging.info(log(f'CAKE: {afterCAKE} CAKE (0)'))

    if(afterARENA < startARENA):
        logging.info(log(f'ARENA: {afterARENA} ARENA (- {startARENA - afterARENA})'))
    elif(afterARENA > startARENA):
        logging.info(log(f'ARENA: {afterARENA} ARENA (+ {afterARENA - startARENA})'))
    else:
        logging.info(log(f'ARENA: {afterARENA} ARENA (0)'))

def tradeSummary(params):
    logging.info('----------------------------------------------')
    logging.info(log(f'Trading Summary: '))
    logging.info('----------------------------------------------')

    usdUsed=0
    
    if(afterBNB < initialBNB):
        usdDiff = convertBNBToUsdtReturnWei(params,initialBNB - afterBNB)/(10**18)
        usdUsed += usdDiff
        logging.info(log(f'BNB: {afterBNB} BNB ( -{initialBNB - afterBNB} BNB) / ( -{usdDiff} USDT)'))
    elif(afterBNB > initialBNB):
        usdDiff = convertBNBToUsdtReturnWei(params,afterBNB - initialBNB)/(10**18)
        usdUsed -= usdDiff
        logging.info(log(f'BNB: {afterBNB} BNB ( +{afterBNB - initialBNB} BNB) / ( +{usdDiff} USDT)'))
    else:
        logging.info(log(f'BNB: {afterBNB} BNB (0)'))

    if(afterCAKE < initialCAKE):
        usdDiff = convertArenaToUsdtReturnWei(params,initialCAKE - afterCAKE)/(10**18)
        usdUsed += usdDiff
        logging.info(log(f'CAKE: {afterCAKE} CAKE ( -{initialCAKE - afterCAKE} CAKE) / ( -{usdDiff} USDT)'))
    elif(afterCAKE > initialCAKE):
        usdDiff = convertArenaToUsdtReturnWei(params,afterCAKE - initialCAKE)/(10**18)
        usdUsed -= usdDiff
        logging.info(log(f'CAKE: {afterCAKE} CAKE (+ {afterCAKE - initialCAKE} CAKE) / ( +{usdDiff} USDT)'))
    else:
        logging.info(log(f'CAKE: {afterCAKE} CAKE (0) '))

    if(afterARENA < initialARENA):
        usdDiff = convertArenaToUsdtReturnWei(params,initialARENA - afterARENA)/(10**18)
        usdUsed += usdDiff
        logging.info(log(f'ARENA: {afterARENA} ARENA ( -{initialARENA - afterARENA} CAKE) / ( -{usdDiff} USDT)'))
    elif(afterARENA > initialARENA):
        usdDiff = convertArenaToUsdtReturnWei(params,afterARENA - initialARENA)/(10**18)
        usdUsed -= usdDiff
        logging.info(log(f'ARENA: {afterARENA} ARENA ( +{afterARENA - initialARENA} CAKE) / ( +{usdDiff} USDT)'))
    else:
        logging.info(log(f'ARENA: {afterARENA} ARENA (0)'))

    logging.info(log(f'Total USD spent (including gas): {usdUsed} USDT'))
    logging.info('----------------------------------------------')



def debuggingModeWaitForSignal(msg):
    if(config.DEBUGGING):
        print(msg)
        x = input()

# Micro Transaction functions
def generateRandIntFromRange(min,max):
    return random.randint(min,max)

def buyMicroTransaction(params,logging,buyTokenAddress,tradeCount,buyVolumeInUSD):
    #how many micro transaction
    microTxCount = generateRandIntFromRange(config.MIN_BUY_MICROTRANSACTION_COUNT,config.MAX_BUY_MICROTRANSACTION_COUNT)
    tradeTokenAmount = pancakeGetPrice(params,[config.USDT_ADDRESS,buyTokenAddress],buyVolumeInUSD)/(10**18)
    initTradeTokenAmount = tradeTokenAmount
    logging.info(log(f'Trade {tradeCount}: {microTxCount} Buy Micro Transaction , buy volume is {buyVolumeInUSD} USD -> {tradeTokenAmount} CAKE token'))
    boughtTokenAmountCumm = 0
    # loop tx
    if( not microTxCount==0 and microTxCount > 1 ):
        # microTxCount = 2 & above
        for txCount in range(microTxCount):
            if(not txCount == (microTxCount-1)):
                percent = generateRandIntFromRange(config.MICROTRANSACTION_PER_TX_LOWER_PERCENTILE,config.MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE)
                microTxBuyAmount = round(tradeTokenAmount*percent/100,5)
                tradeTokenAmount -= microTxBuyAmount
                [buy,boughtTokenAmount] = buyTokens(params,microTxBuyAmount,logging)
                boughtTokenAmountCumm += boughtTokenAmount
                logging.info(log(buy))
                logging.info(log(f' Trade {tradeCount} mTx {txCount+1}: after buy, {microTxBuyAmount} CAKE for {boughtTokenAmount} ARENA, Remaining {tradeTokenAmount} CAKE to go'))
            else:
                [buy,boughtTokenAmount] = buyTokens(params,tradeTokenAmount,logging)
                boughtTokenAmountCumm += boughtTokenAmount
                logging.info(log(buy))
                logging.info(log(f' Trade {tradeCount} last mTx {txCount+1}: after buy, {tradeTokenAmount} CAKE for {boughtTokenAmount} ARENA'))
    else:
        # microTxCount = 1 & above
        if(microTxCount ==1):
            [buy,boughtTokenAmount] = buyTokens(params,tradeTokenAmount,logging)
            boughtTokenAmountCumm += boughtTokenAmount
            logging.info(log(buy))
            logging.info(log(f' Trade {tradeCount} mTx {microTxCount}: after buy, {tradeTokenAmount} CAKE for {boughtTokenAmount} ARENA'))
        else:
            logging.info(log(f' Trade {tradeCount} mTx {0}: No Trade for this round'))
            raise Exception('Micro Transaction must have at least 1 transaction')

    return initTradeTokenAmount,boughtTokenAmountCumm

def sellMicroTransaction(params,logging,sellTokenAddress,tradeCount,sellVolumeInUSD):
    #how many micro transaction
    microTxCount = generateRandIntFromRange(config.MIN_SELL_MICROTRANSACTION_COUNT,config.MAX_SELL_MICROTRANSACTION_COUNT)
    tradeTokenAmount = pancakeGetPrice(params,[config.USDT_ADDRESS,sellTokenAddress],sellVolumeInUSD)/(10**18)
    initTradeTokenAmount = tradeTokenAmount
    logging.info(log(f'Trade {tradeCount}: Sell Micro Transaction {microTxCount}, sell volume is {sellVolumeInUSD} USD -> {tradeTokenAmount} ARENA token'))
    boughtTokenAmountCumm = 0
    # loop tx
    if( not microTxCount==0 and microTxCount > 1 ):
        # microTxCount = 2 & above
        for txCount in range(microTxCount):
            if(not txCount == (microTxCount-1)):
                percent = generateRandIntFromRange(config.MICROTRANSACTION_PER_TX_LOWER_PERCENTILE,config.MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE)
                microTxSellAmount = round(tradeTokenAmount*percent/100,5)
                tradeTokenAmount -= microTxSellAmount
                [sell,boughtTokenAmount] = sellTokens(params,microTxSellAmount,logging)
                boughtTokenAmountCumm += boughtTokenAmount
                logging.info(log(sell))
                logging.info(log(f' Trade {tradeCount} mTx {txCount+1}: after sell, {microTxSellAmount} ARENA for {boughtTokenAmount} CAKE, Remaining {tradeTokenAmount} ARENA to go'))
            else:
                [sell,boughtTokenAmount] = sellTokens(params,tradeTokenAmount,logging)
                boughtTokenAmountCumm += boughtTokenAmount
                logging.info(log(sell))
                logging.info(log(f' Trade {tradeCount} last mTx {txCount+1}: after sell, {tradeTokenAmount} ARENA for {boughtTokenAmount} CAKE'))
    else:
        # microTxCount = 1 & above
        if(microTxCount ==1):
            [buy,boughtTokenAmount] = sellTokens(params,tradeTokenAmount,logging)
            boughtTokenAmountCumm += boughtTokenAmount
            logging.info(log(buy))
            logging.info(log(f' Trade {tradeCount} mTx {microTxCount}: after buy, {tradeTokenAmount} ARENA for {boughtTokenAmount} CAKE'))
        else:
            logging.info(log(f' Trade {tradeCount} mTx {0}: No Trade for this round'))
            raise Exception('Micro Transaction must have at least 1 transaction')

    return initTradeTokenAmount,boughtTokenAmountCumm


# def sellMicroTransaction():

def tradeToken(params):
    global tradeCount,tradeVolume, latestSoldArenaForCake,latestBuyAreaWithCake
    if(tradeVolume <=0):
        logging.info(log(f'Trading completed, stop the trade schedule'))
        schedule.cancel_job(tradeCycleJob)
        logging.info(log(f'Cancelled Job, The ENd'))
        tradeSummary(params)
        # exit script
        sys.exit()

    else:
        logging.info('---------------------------')
        
        [startBNB,startCAKE,startARENA] = startTradeWalletBalanceReport()

        # generate one time trading volume ( buy & sell volume = trade volume /2 )
        tradeEtherAmountUsd =  generateRandIntFromRange(config.PER_TRANSACTION_VOLUME_LOWER_USD,config.PER_TRANSACTION_VOLUME_UPPER_USD)

        if(tradeEtherAmountUsd > tradeVolume and tradeVolume >0):  
            tradeEtherAmountUsd = tradeVolume


        tradeCount +=1

        logging.info(log(f'Trade {tradeCount}: buy trade volume: {tradeEtherAmountUsd/2} USD worth of ARENA, current remaining trade volume {tradeVolume-tradeEtherAmountUsd/2} USD'))

        debuggingModeWaitForSignal('start buy?')

        [spentCAKE,boughtARENA]= buyMicroTransaction(params,logging,config.ARENA_ADDRESS,tradeCount,tradeEtherAmountUsd/2)
        latestBuyArenaWithCake = boughtARENA
        logging.info(log(f' Trade {tradeCount}: after buy, {spentCAKE} CAKE for {latestBuyArenaWithCake} ARENA'))
        tradeVolume -= tradeEtherAmountUsd/2

        debuggingModeWaitForSignal('start sell?')
        logging.info('------')
        logging.info(log(f'Trade {tradeCount}: sell trade volume: {tradeEtherAmountUsd/2} USD worth of CAKE, current remaining trade volume {tradeVolume-tradeEtherAmountUsd/2} USD'))
        [spentARENA,boughtCAKE]= sellMicroTransaction(params,logging,config.CAKE_ADDRESS,tradeCount,tradeEtherAmountUsd/2)
        latestSoldArenaForCake = boughtCAKE
        logging.info(log(f' Trade {tradeCount}: after sell, {spentARENA} ARENA for {latestSoldArenaForCake} CAKE'))

        logging.info(log(f' Trade {tradeCount}: end trade {spentARENA} ARENA, {latestSoldArenaForCake} CAKE'))
        tradeVolume -= tradeEtherAmountUsd/2

        returnMsg=f'Trade Cycle: {tradeCount}, Traded {latestBuyArenaWithCake} CAKE & {latestSoldArenaForCake} Arena with {tradeEtherAmountUsd/2} USD, traded volume: {tradeEtherAmountUsd} USD,'
        remainingTradeMsg = f'left {tradeVolume} USD to go' if not tradeVolume < 0 else f' no remaining volume'
        logging.info(log(returnMsg + remainingTradeMsg))

        endTradeWalletBalanceReport(startBNB,startCAKE,startARENA)

def runCode():

    BNB_balance, TokenSymbol, NoOfTokens, params = InitializeTrade()

    # set initial trade amount usdt to cake
    global latestBuyAreaWithCake,tradeCycleJob

    tradeCycleJob = schedule.every(15).seconds.do(tradeToken,params) # not recommended to put below 30s, buy sell have a delay of 5s for transaction verification

    bnb = web3.eth.get_balance(walletAddress)

    global initialBNB,initialCAKE,initialARENA
    initialBNB= web3.fromWei(bnb, 'ether')
    initialCAKE= CakeToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)
    initialARENA= ArenaToken.getBalanceInWei(config.YOUR_WALLET_ADDRESS)/(10**18)
    configCheck()

    while True:
       schedule.run_pending()

if __name__ == "__main__":
    print('starting...')
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
