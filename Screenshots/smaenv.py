import alpaca_backtrader_api
import backtrader as bt
from datetime import datetime
from _datetime import timedelta
from dotenv import load_dotenv
import os



# Your credentials here
load_dotenv()
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")



# Modes you can run this script. 
# How to use:
"""
You have 3 options: 
 - backtest (IS_BACKTEST=True, IS_LIVE=False)
 - paper trade (IS_BACKTEST=False, IS_LIVE=False) 
 - live trade (IS_BACKTEST=False, IS_LIVE=True) 
"""



IS_BACKTEST = False
IS_LIVE = False

# Traded symbol
symbol = "SPY"
# For live account only
USE_POLYGON = False



# This part is strategy code, logic, executions, logging.
# For each strategy different class
class SmaCross1(bt.Strategy):

    # Notifications functions of API  status. Like, live data or delayed
    def notify_fund(self, cash, value, fundvalue, shares):
        super().notify_fund(cash, value, fundvalue, shares)

    def notify_store(self, msg, *args, **kwargs):
        super().notify_store(msg, *args, **kwargs)

    def notify_data(self, data, status, *args, **kwargs):
        super().notify_data(data, status, *args, **kwargs)
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if data._getstatusname(status) == "LIVE":
            self.live_bars = True

    
    # list of parameters which are configurable for the strategy
    # set your length of MA
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30   # period for the slow moving average
    )

    # just for logging
    def log(self, txt, dt=None):
        dt = dt or self.data.datetime[0]
        dt = bt.num2date(dt)
        print('%s, %s' % (dt.isoformat(), txt))

    # Notifications functions for executions
    def notify_trade(self, trade):
        self.log("placing trade for {}. target size: {}".format(
            trade.getdataname(),
            trade.size))

    def notify_order(self, order):
        print(f"Order notification. status{order.getstatusname()}.")
        print(f"Order info. status{order.info}.")


    # Notifications function for portfolio info. Called at the end of script.
    def stop(self):
        print('==================================================')
        print('Starting Value - %.2f' % self.broker.startingcash)
        print('Ending   Value - %.2f' % self.broker.getvalue())
        print('==================================================')


    # Intitialing params for your strategy
    def __init__(self):
        self.live_bars = False
        # SMA indicators
        self.sma1 = bt.ind.SMA(self.data0, period=self.p.pfast)
        self.sma2 = bt.ind.SMA(self.data0, period=self.p.pslow)
        # Crossover indicator
        self.crossover0 = bt.ind.CrossOver(self.sma1, self.sma2)

        # timer is used for dividing event for timeframe
        self.timer = datetime.utcnow()

    # Main loop of algorithm. 
    # Called by every event in real-time mode or bar timeframe in backtesting mode. 
    # Your logic strategy inside.
    # To see any additional logs, just add some your logs inside this function
    # For example, to see current price: self.data0[0]
    def next(self):
        # Current instrument(ticker). It get from DataFactory's dataname param
        print("Current ticker:", self.data._name)
        # Last trade price
        print("Last trade price with time:")
        self.log(self.data0.close[0])
        # set your timeframe by timedelta() params
        # For intraday  timeframes - minutes=
        # For days - day=
        # wait until time left
        if datetime.utcnow() - self.timer < timedelta(minutes=1):
            return
        # then after time is trigger run your logic
        self.timer = datetime.utcnow()

        # Logic and execution
        # if fast crosses slow to the upside and no in the market (no opened position)
        if not self.positionsbyname[symbol].size and self.crossover0 > 0:
            # send buy order
            self.buy(data=data0, size=5)  # enter long
        
        # opposite logic
        if not self.positionsbyname[symbol].size and self.crossover0 < 0:
            # send buy order
            self.sell(data=data0, size=5)  # enter short
        

        # closing position
        # in the market & cross to the downside
        if self.positionsbyname[symbol].size and self.crossover0 <= 0:
            self.close(data=data0)  # close long position



# Broker part
if __name__ == '__main__':
    import logging
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    # This is core of framework, like broker manager. With this you can use supported brokers, like IB or Alpaca in our case. See line 150
    cerebro = bt.Cerebro()

    # Adding your strategy (from class) to framework
    cerebro.addstrategy(SmaCross1)

    store = alpaca_backtrader_api.AlpacaStore(
        key_id=ALPACA_API_KEY,
        secret_key=ALPACA_SECRET_KEY,
        paper=not IS_LIVE,
        usePolygon=USE_POLYGON
    )

    # DataFactory is like data manager for your instrument (ticker). You can use Alpaca feed, local file or Polygon.io
    # There are a lot of params, but main thing is in what mode you're want to use framework. 
    # If backtesting mode - you need switch  historical to True and select date range.
    # DataFactory returns data feed
    DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData
    if IS_BACKTEST:
        data0 = DataFactory(dataname=symbol,
                            historical=True,
                            fromdate=datetime(2020, 7, 1),
                            todate=datetime(2020, 7, 11),
                            timeframe=bt.TimeFrame.Days)
    else:
        data0 = DataFactory(dataname=symbol,
                            historical=False,
                            timeframe=bt.TimeFrame.Minutes,
                            fromdate=datetime(2020, 7, 11),
                            backfill_start=False,
                            )

        # Set Alpaca broker to framework
        # or just alpaca_backtrader_api.AlpacaBroker()
        broker = store.getbroker()
        cerebro.setbroker(broker)
    
    # Adding data feed to broker
    cerebro.adddata(data0)

    # In backtesting mode you can't use third-party broker. So need to use backtrader broker.
    if IS_BACKTEST:
        # backtrader broker set initial simulated cash
        cerebro.broker.setcash(100000.0)

    print('Starting Portfolio Value: {}'.format(cerebro.broker.getvalue()))
    cerebro.run()
    print('Final Portfolio Value: {}'.format(cerebro.broker.getvalue()))
    cerebro.plot()