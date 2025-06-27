# logic:
# in the current candle.
# set one variable: stop_profit_num (initialize it with 50)
# give me entry signal the previous three candles are the any of this following order: (bear, bear, bull) or (bull, bull, bear)
# A:if (bear, bear, bull): then we check if the bull's low is less than the previous two bears' lows, 
# if previous condition is true then we check if the bull's close is greater than the previous two bears' opens.
# then give buy signal on the current candel.
# set stop loss at the low of the bull candle.
# set stop profit price at the current candle's open + stop_profit.
# B:if (bull, bull, bear): then we check if the bear's high is greater than the previous two bulls' highs,
# if previous condition is true then we check if the bear's close is less than the previous two bulls' opens.
# then give sell signal on the current candel.
# set stop loss at the high of the bear candle.
# set stop profit price at the current candle's open - stop_profit.



import pandas as pd

stop_profit_num = 100
stop_loss_num = 50

# Load your data
df = pd.read_csv('NQ_15_new_clean.csv')

# Ensure column names are lowercase
df.columns = [col.lower() for col in df.columns]

# Combine date and time into a datetime column for easier handling
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])

# Determine candle type
def candle_type(row):
    if row['close'] > row['open']:
        return 'bull'
    elif row['close'] < row['open']:
        return 'bear'
    else:
        return 'doji'

df['candle'] = df.apply(candle_type, axis=1)

trades = []
in_trade = False
trade = {}

for i in range(3, len(df)):
    if not in_trade:
        prev3 = df.iloc[i-3:i]
        c1, c2, c3 = prev3['candle'].values
        # A: (bear, bear, bull)
        if (c1 == 'bear' and c2 == 'bear' and c3 == 'bull'):
            if (prev3.iloc[2]['low'] < prev3.iloc[0]['low'] and prev3.iloc[2]['low'] < prev3.iloc[1]['low']):
                if (prev3.iloc[2]['close'] > prev3.iloc[0]['open'] and prev3.iloc[2]['close'] > prev3.iloc[1]['open']):
                    entry_idx = i
                    entry_price = df.iloc[i]['open']
                    stop_loss = prev3.iloc[2]['low']
                    stop_profit = entry_price + stop_profit_num
                    trade = {
                        'type': 'buy',
                        'entry_idx': entry_idx,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'stop_profit': stop_profit
                    }
                    in_trade = True
        # B: (bull, bull, bear)
        elif (c1 == 'bull' and c2 == 'bull' and c3 == 'bear'):
            if (prev3.iloc[2]['high'] > prev3.iloc[0]['high'] and prev3.iloc[2]['high'] > prev3.iloc[1]['high']):
                if (prev3.iloc[2]['close'] < prev3.iloc[0]['open'] and prev3.iloc[2]['close'] < prev3.iloc[1]['open']):
                    entry_idx = i
                    entry_price = df.iloc[i]['open']
                    stop_loss = prev3.iloc[2]['high']
                    stop_profit = entry_price - stop_profit_num
                    trade = {
                        'type': 'sell',
                        'entry_idx': entry_idx,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'stop_profit': stop_profit
                    }
                    in_trade = True
    else:
        # Trade management: check each candle after entry for stop loss or stop profit
        for j in range(i, len(df)):
            row = df.iloc[j]
            if trade['type'] == 'buy':
                # Stop loss first, then stop profit
                if row['low'] <= trade['stop_loss']:
                    exit_price = trade['stop_loss']
                    profit = exit_price - trade['entry_price']
                    trades.append({
                        'type': 'buy',
                        'entry_date': df.iloc[trade['entry_idx']]['date'],
                        'entry_time': df.iloc[trade['entry_idx']]['time'],
                        'entry_price': trade['entry_price'],
                        'exit_date': row['date'],
                        'exit_time': row['time'],
                        'exit_price': exit_price,
                        'profit': profit
                    })
                    in_trade = False
                    trade = {}
                    i = j  # Continue from this bar
                    break
                elif row['high'] >= trade['stop_profit']:
                    exit_price = trade['stop_profit']
                    profit = exit_price - trade['entry_price']
                    trades.append({
                        'type': 'buy',
                        'entry_date': df.iloc[trade['entry_idx']]['date'],
                        'entry_time': df.iloc[trade['entry_idx']]['time'],
                        'entry_price': trade['entry_price'],
                        'exit_date': row['date'],
                        'exit_time': row['time'],
                        'exit_price': exit_price,
                        'profit': profit
                    })
                    in_trade = False
                    trade = {}
                    i = j  # Continue from this bar
                    break
            elif trade['type'] == 'sell':
                # Stop loss first, then stop profit
                if row['high'] >= trade['stop_loss']:
                    exit_price = trade['stop_loss']
                    profit = trade['entry_price'] - exit_price
                    trades.append({
                        'type': 'sell',
                        'entry_date': df.iloc[trade['entry_idx']]['date'],
                        'entry_time': df.iloc[trade['entry_idx']]['time'],
                        'entry_price': trade['entry_price'],
                        'exit_date': row['date'],
                        'exit_time': row['time'],
                        'exit_price': exit_price,
                        'profit': profit
                    })
                    in_trade = False
                    trade = {}
                    i = j  # Continue from this bar
                    break
                elif row['low'] <= trade['stop_profit']:
                    exit_price = trade['stop_profit']
                    profit = trade['entry_price'] - exit_price
                    trades.append({
                        'type': 'sell',
                        'entry_date': df.iloc[trade['entry_idx']]['date'],
                        'entry_time': df.iloc[trade['entry_idx']]['time'],
                        'entry_price': trade['entry_price'],
                        'exit_date': row['date'],
                        'exit_time': row['time'],
                        'exit_price': exit_price,
                        'profit': profit
                    })
                    in_trade = False
                    trade = {}
                    i = j  # Continue from this bar
                    break

# Output trades and total profit
trades_df = pd.DataFrame(trades)
print(trades_df)
print(f"Total profit: {trades_df['profit'].sum()}")

win_rate = (trades_df['profit'] > 0).sum() / len(trades_df)
print(f"Win rate: {win_rate:.2%}")

# Save to CSV
trades_df.to_csv('executed_trades.csv', index=False)
