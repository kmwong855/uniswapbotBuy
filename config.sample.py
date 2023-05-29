YOUR_WALLET_ADDRESS = ""  # Add Your Wallet Address here by removing whole line
YOUR_PRIVATE_KEY = ""  # Add Your Private Key here by removing whole line

ARENA_ADDRESS = "0xCfFD4D3B517b77BE32C76DA768634dE6C738889B"  # ARENA
CAKE_ADDRESS = "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"       # CAKE
APESWAP_ROUTER_ADDRESS = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

SELL_TOKENS = True  # enable sell tokens
BUY_TOKENS = True  # enable buy tokens

RPC_URL = 'https://bsc-dataseed.binance.org/'
# now change to crontab, everytime run a fix amount of trade trigger by system
# therefore   INITIAL_BUY_USDT_AMOUNT_IN_ETHER must = TRADE_VOLUME_LIMIT_HALF
INITIAL_BUY_USDT_AMOUNT_IN_ETHER =
TRADE_VOLUME_LIMIT_HALF =  # volume in USD, unit Ether not wei

WAIT_FOR_TX_RECEIPT_TIMEMOUT_SECONDS = 120
WAIT_FOR_TX_RECEIPT_POLL_FREQUENCY = 0.1
GAS_PRICE_IN_WEI = 6

# Micro Transaction Parameters
# basically split one big transaction volume into rand small micro trasaction
PER_TRANSACTION_VOLUME_UPPER = 4
PER_TRANSACTION_VOLUME_LOWER = 1

# Buy
MAX_BUY_MICROTRANSACTION_COUNT = 5
MIN_BUY_MICROTRANSACTION_COUNT = 3

# SELL
MAX_SELL_MICROTRANSACTION_COUNT = 1
MIN_SELL_MICROTRANSACTION_COUNT = 1

MICROTRANSACTION_PER_TX_UPPPER_PERCENTILE = 75  # %
MICROTRANSACTION_PER_TX_LOWER_PERCENTILE = 25  # %

# random percentage will be picked between PER_TRANSACTION_VOLUME_LOWER_USD & PER_TRANSACTION_VOLUME_UPPER_USD
# MICROTRANSACTION_COUNT = 3
# PER_TRANSACTION_VOLUME = 500
# Buy 500/2 = 250USD Sell 500/2 = 250USD

# MICROTRANSACTION_PER_TX = 45%, random between 25-75
# Tx1 = 500 x 45%  = First Buy Amount

# MICROTRANSACTION_PER_TX = 38%, random between 25-75
# Tx2 = (500 - Tx1 ) x 38% = Second Buy Amonut
# Tx3 = (500 - Tx1 - Tx2) = Third Buy Amonut
# Same goes to SELL

# to enable manual mode & override tx receipt with pre defined tx hash if set to true
DEBUGGING = False
SLIPPAGE = 0.3  # not in use currently
