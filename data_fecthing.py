from ib_insync import *
import datetime
# util.startLoop()  # uncomment this line when in a notebook

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

end = datetime.datetime(year=2005, month=1, day=1, hour=0, minute=0)

contract = Stock(symbol='TSLA', exchange='SMART', currency='USD')
q_c = ib.qualifyContracts(contract)
print(q_c)

bars = ib.reqHistoricalData(
    contract, endDateTime='', durationStr='3 D',
    barSizeSetting='1 min', whatToShow='Adjusted_last', useRTH= True, timeout= 0)

df = util.df(bars)
df.to_csv('test.csv', index=False)
print('done')