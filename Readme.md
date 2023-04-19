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


