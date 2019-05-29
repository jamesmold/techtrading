import pyEX as p
import pandas as pd
from statistics import stdev
import time
import smtplib

stockfile = open("stocks.csv")
watchlist = []
for stock in stockfile:
        stock = stock.strip()
        watchlist.append(stock)

df = pd.DataFrame(columns = ['Date'])

def chart(stock): #downloads the price chart for each stock
    close_label = stock+'Close'
    vwap_label = stock+'vWAP'
    chart = p.chart(stock, '5y')
    print("STOCK DATA DOWNLOADING..", stock)
    global chartlen
    chartlen = len(chart)
    daycount = 0
    for day in reversed(chart):
        df.loc[daycount, 'Date'] = day['date']
        df.loc[daycount, close_label] = day['close']
        df.loc[daycount, vwap_label] = day['vwap']
        daycount += 1

def ema(days, stock): #calcs the exponential moving averages
    close_label = stock+'Close'
    ema_label = stock+str(days)+'dEMA'
        
    mult = 2/(days + 1)
    df.loc[chartlen-days, ema_label] = df.loc[chartlen-days:chartlen,close_label].mean()
    for i in range(chartlen-days-1,-1,-1):
        df.loc[i, ema_label] = (df.loc[i, close_label]*mult)+(df.loc[i+1,ema_label]*(1-mult))

def macd(stock): #cals the moving average convergence/divergence
    macd_label = stock+'MACD'

    for i in range(chartlen-26,-1,-1):
        df.loc[i, macd_label] = df.loc[i, stock+'12dEMA'] - df.loc[i, stock+'26dEMA']

def signal(stock): #calcs the signal line
    signal_label = stock+'Signal'
    macd_label = stock+'MACD'

    df.loc[1224, signal_label] = df.loc[1224:1232, macd_label].mean()
    for i in range(1223,-1,-1):
        df.loc[i, signal_label] = (df.loc[i, macd_label]*(2/10))+(df.loc[i+1, signal_label]*(1-(2/10)))

def gainloss(stock): #determines if the stock made a gain/loss day on day
    gain_label = stock+'Gain'
    loss_label = stock+'Loss'
    close_label = stock+'Close'

    for i in range(chartlen-1,0,-1):
        if df.loc[i-1, close_label] > df.loc[i, close_label]:
            df.loc[i-1, gain_label] = df.loc[i-1, close_label] - df.loc[i, close_label]
            df.loc[i-1, loss_label] = 0
        elif df.loc[i-1, close_label] < df.loc[i, close_label]:
            df.loc[i-1, loss_label] = df.loc[i, close_label] - df.loc[i-1, close_label]
            df.loc[i-1, gain_label] = 0
        else:
            df.loc[i-1, gain_label] = 0
            df.loc[i-1, loss_label] = 0

def movavg(stock): #calcs the 50d and 200d average prices
    mov50_label = stock+'50d'
    mov200_label = stock+'200d'
    vwap_label = stock+'vWAP'

    for i in range(chartlen-50):
        df.loc[i, mov50_label] = df.loc[i:i+50, vwap_label].mean()

    for i in range(chartlen-200):
        df.loc[i, mov200_label] = df.loc[i:i+200, vwap_label].mean()

def rsicalc(stock): #calcs the relative strength index
    gain_label = stock+'Gain'
    loss_label = stock+'Loss'
    avgain_label = stock+'AvgGain'
    avloss_label = stock+'AvgLoss'
    rsi_label = stock+'RSI'

    df.loc[chartlen-14, avgain_label] = df.loc[chartlen-14:chartlen, gain_label].mean()
    df.loc[chartlen-14, avloss_label] = df.loc[chartlen-14:chartlen, loss_label].mean()
    for i in range(chartlen-15,-1,-1):
        df.loc[i, avgain_label] = ((df.loc[i+1, avgain_label]*13)+df.loc[i, gain_label])/14
        df.loc[i, avloss_label] = ((df.loc[i+1, avloss_label]*13)+df.loc[i, loss_label])/14
        rs = df.loc[i, avgain_label] / df.loc[i, avloss_label]
        df.loc[i,rsi_label] = round(100 - 100/(1+rs), 2)

def bollinger(stock): #calcs the bollinger bands
    sd_label = stock+'20dSD'
    close_label = stock+'Close'
    mid_label = stock+'Mid'
    upp_label = stock+'Upp'
    low_label = stock+'Low'

    for i in range(chartlen-20):
        df.loc[i, sd_label] = stdev(df.loc[i:i+19, close_label])
        df.loc[i, mid_label] = df.loc[i:i+20, close_label].mean()
        df.loc[i, upp_label] = df.loc[i, mid_label]+(df.loc[i, sd_label]*2)
        df.loc[i, low_label] = df.loc[i, mid_label]-(df.loc[i, sd_label]*2)

def movavgind(stock): #determines the buy/sell indicator based on 50d and 200d average prices
    movavgind_label = stock+'-MVAVGInd'
    mov50_label = stock+'50d'
    mov200_label = stock+'200d'

    for i in range(chartlen):
        if df.loc[i, mov50_label] > df.loc[i, mov200_label]:
            df.loc[i,movavgind_label] = "Buy"
        else:
            df.loc[i,movavgind_label] = "Sell"

def macdind(stock): #determines the buy/sell indicator based on MACD
    macdind_label = stock+'-MACDInd'
    signal_label = stock+'Signal'
    macd_label = stock+'MACD'
    
    for i in range(chartlen):
        if df.loc[i, macd_label] > df.loc[i, signal_label]:
            df.loc[i,macdind_label] = "Buy"
        else:
            df.loc[i,macdind_label] = "Sell"

def rsiind(stock): #determines the buy/sell indicator based on RSI
    rsiind_label = stock+'-RSInd'
    rsi_label = stock+'RSI'
    
    for i in range(chartlen):
        if df.loc[i,rsi_label] > 70:
            df.loc[i,rsiind_label] = "Sell"
        elif df.loc[i,rsi_label] < 30:
            df.loc[i,rsiind_label] = "Buy"
        else:
            df.loc[i,rsiind_label] = "Hold"

def bollind(stock): #determines the buy/sell indicator based on boliinger bands
    bollind_label = stock+'-BollInd'
    mid_label = stock+'Mid'
    low_label = stock+'Low'
    close_label = stock+'Close'

    for i in range(chartlen):
        if df.loc[i, close_label] > df.loc[i, mid_label]:
            df.loc[i, bollind_label] = "Sell"
        elif df.loc[i, close_label] < df.loc[i, low_label]:
            df.loc[i, bollind_label] = "Buy"
        else:
            df.loc[i, bollind_label] = "Hold"
 
stkcnt = 0 #runs the code for each stock
for stock in watchlist:
    stkcnt += 1
    stock = stock.strip()
    print("No. ", stkcnt, "Attempting: ", stock)
    try:
        chart(stock)
        for days in (12,26):
            ema(days, stock)
        macd(stock)
        signal(stock)
        gainloss(stock)
        movavg(stock)
        rsicalc(stock)
        bollinger(stock)
        movavgind(stock)
        macdind(stock)
        rsiind(stock)
        bollind(stock)
    except:
        pass

# print(df) -- to see the whole dataframe
df = df.filter(like='Ind', axis=1)
collist = df.columns.values.tolist()
emaillist = []
# print(df) - to see just the indicators

for i in range(0,27688,4): #builds a list of buy/sell indicator counts > 2 per stock, to include in the email
    group = df.iloc[0, i:i+4]
    buycount = 0
    sellcount = 0
    for ind in group:
        if ind == "Buy":
            buycount += 1
        if ind == "Sell":
            sellcount += 1
    if buycount > 2 or sellcount > 2:
        emaillist.append((collist[i].split('-')[0], "Buy:", buycount, "Sell:", sellcount))

# prepares and eends the email
user = 'me@gmail.com'  
password = 'myemailpassword'

sent_from = user
to = ['you@gmail.com']
subject = 'Tech Analysis - WatchList'  
body = '\n'.join(str(v) for v in emaillist)

email_text = """\
From: %s  
To: %s  
Subject: %s

%s
""" % (sent_from, ", ".join(to), subject, body)

server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.ehlo()
server.login(user, password)
server.sendmail(sent_from, to, email_text)
server.close()