# Installation
1. install python for windows
2. run: python -m venv defi-env
3. run: pip install -r requirement.ext
4. copy config.sample.py to config.py
5. update all the parameters inside config.py
5. run: python DeFiTransaction.py

extra notes:
1. if pip got any problem, install one by one
2. make sure wallet has max approval on both BNB and ARENA token

## Prod
1. make sure all tokens are 18 decimals, code assume all token uses 18 decimals
2. make sure all tokens has max approval amount on pancake router, else transaction might fail
3. there is no acceptable min token amount for trade, min is 1wei to submit trasaction easily, so long as > 1wei the code agree to trade any token, kind of dangerous but else require some +-% conversion calculation
5. no balance fund check, insufficient fund the code will still proceed and burn gas even till the trasaction failed halfway



## Window Scheduling guide
launch Window Task Scheduler, create new Basic task, with:

General
-Run Only when user logged in / Run Whether
-Run with highest priviledges

Triggers
- One time, repeat every hour
- make sure enabled

Actions
-choose start a program
-Insert Program / script:
"C:\Users\Bryant\AppData\Local\Programs\Python\Python310\python.exe"  your path might be differnt on different machine & different version of python
-Insert Add arguments:
DeFiTranscation.py
-Start in:
C:\Users\Bryant\Desktop\pancakebot

Conditions
-uncheck all
-depending situation whether power & network setting is needed or not

Setting
-Since this script only run one trasaction once triggered, if the task is running it shouldn't start a new instance


# Config File
// Add Your Wallet Address here by removing whole line
YOUR_WALLET_ADDRESS = [
]

// Add Your Private Key here by removing whole line
YOUR_PRIVATE_KEY = [
]

XPEPE_ADDRESS = "0x91eEB5337b06C4cf0C5a5d73e326F99a0015aED1"

ROUTER_ADDRESS = "0xE592427A0AEce92De3Edee1F18E0157C05861564"  # SUSHISWAP ROUTER

USDT_ADDRESS = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"  # USDC
 
RPC_URL = "https://arb1.arbitrum.io/rpc"

WAIT_FOR_TX_RECEIPT_TIMEMOUT_SECONDS = 120
WAIT_FOR_TX_RECEIPT_POLL_FREQUENCY = 0.1
GAS_PRICE_IN_WEI = 6

// Micro Transaction Parameters
// basically split one big transaction volume into rand small micro trasaction
PER_TRANSACTION_VOLUME_UPPER = 1
PER_TRANSACTION_VOLUME_LOWER = 1

// Buy
MAX_BUY_MICROTRANSACTION_COUNT = 5
MIN_BUY_MICROTRANSACTION_COUNT = 3

// SELL
MAX_SELL_MICROTRANSACTION_COUNT = 1
MIN_SELL_MICROTRANSACTION_COUNT = 1

MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE = 3  # %
MICROTRANSACTION_PER_TX_LOWER_PERCENTILE = 1  # %

// to enable manual mode & override tx receipt with pre defined tx hash if set to true
DEBUGGING = False
SLIPPAGE = 0.3  # not in use currently

TOTAL_TRADE_VOLUME = 2

ADDRESS_GROUPING = 10

WALLET_COUNT = 2


