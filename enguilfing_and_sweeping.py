import pandas as pd
import talib

#initialize a risk reward parameter, set it initially to 2.5
#now we have identify the engulfing candles and set alarms for the next candle
#for bullish engulfing, we will enter the trade at the open price of next candle(alarm candle),
#we set the stop loss at the low of the engulfing candle, and set take profit as entry price + (entry price - stop loss) * risk_reward_ratio
#for bearish engulfing, we will enter the trade at the open price of next candle(alarm candle),
# we set the stop loss at the high of the engulfing candle, and set take profit as entry price - (stop loss - entry price) * risk_reward_ratio

risk_reward_ratio = 2.5

# Load the CSV
# df = pd.read_csv("NQ_data_cont/NQ_1min.csv")
df = pd.read_csv("TSLA_10Y_1m.csv")
#df = pd.read_csv('Engulf_sweeping/NQ_15_new_clean.csv')

# Ensure data is sorted by date and time
df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
df = df.sort_values('datetime').reset_index(drop=True)

# Create the alarm column
df['alarm'] = ''

# Add columns for entry, stop loss, and take profit
df['entry'] = None
df['stop_loss'] = None
df['take_profit'] = None

# Loop through the dataframe
for i in range(1, len(df)):
    prev = df.loc[i - 1]
    cur = df.loc[i]

    # Check if current candle is bullish
    if cur['close'] > cur['open']:
        if cur['low'] < prev['low'] and cur['close'] > max(prev['open'], prev['close']):
            # Set 'buy' on the NEXT candle (i+1), if it exists
            if i + 1 < len(df):
                df.at[i + 1, 'alarm'] = 'buy'
                entry = df.loc[i + 1, 'open']
                stop_loss = cur['low']
                take_profit = entry + (entry - stop_loss) * risk_reward_ratio
                df.at[i + 1, 'entry'] = entry
                df.at[i + 1, 'stop_loss'] = stop_loss
                df.at[i + 1, 'take_profit'] = take_profit

    # Check if current candle is bearish
    elif cur['close'] < cur['open']:
        if cur['high'] > prev['high'] and cur['close'] < min(prev['open'], prev['close']):
            # Set 'sell' on the NEXT candle (i+1), if it exists
            if i + 1 < len(df):
                df.at[i + 1, 'alarm'] = 'sell'
                entry = df.loc[i + 1, 'open']
                stop_loss = cur['high']
                take_profit = entry - (stop_loss - entry) * risk_reward_ratio
                df.at[i + 1, 'entry'] = entry
                df.at[i + 1, 'stop_loss'] = stop_loss
                df.at[i + 1, 'take_profit'] = take_profit

trade_list = []
in_trade = False
i = 0

while i < len(df):
    if not in_trade and df.at[i, 'alarm'] in ['buy', 'sell']:
        trade_type = df.at[i, 'alarm']
        entry_price = df.at[i, 'entry']
        stop_loss = df.at[i, 'stop_loss']
        take_profit = df.at[i, 'take_profit']
        entry_date = df.at[i, 'Date']
        entry_time = df.at[i, 'Time']
        entry_volume = df.at[i, 'volume']  # Get entry volume

        # Simulate the trade: check each subsequent candle for SL/TP hit
        exit_price = None
        exit_date = None
        exit_time = None
        exit_volume = None
        for j in range(i + 1, len(df)):
            low = df.at[j, 'low']
            high = df.at[j, 'high']
            if trade_type == 'buy':
                if low <= stop_loss:
                    exit_price = stop_loss
                    exit_date = df.at[j, 'Date']
                    exit_time = df.at[j, 'Time']
                    exit_volume = df.at[j, 'volume']
                    break
                if high >= take_profit:
                    exit_price = take_profit
                    exit_date = df.at[j, 'Date']
                    exit_time = df.at[j, 'Time']
                    exit_volume = df.at[j, 'volume']
                    break
            elif trade_type == 'sell':
                if high >= stop_loss:
                    exit_price = stop_loss
                    exit_date = df.at[j, 'Date']
                    exit_time = df.at[j, 'Time']
                    exit_volume = df.at[j, 'volume']
                    break
                if low <= take_profit:
                    exit_price = take_profit
                    exit_date = df.at[j, 'Date']
                    exit_time = df.at[j, 'Time']
                    exit_volume = df.at[j, 'volume']
                    break

        # If neither SL nor TP is hit, close at last available price
        if exit_price is None:
            exit_price = df.at[len(df) - 1, 'close']
            exit_date = df.at[len(df) - 1, 'Date']
            exit_time = df.at[len(df) - 1, 'Time']
            exit_volume = df.at[len(df) - 1, 'volume']

        profit = exit_price - entry_price if trade_type == 'buy' else entry_price - exit_price

        trade_list.append({
            'trade': trade_type,
            'entry_date': entry_date,
            'entry_time': entry_time,
            'entry_price': entry_price,
            'entry_volume': entry_volume,      # Add entry volume
            'stop_loss': stop_loss,            # Add stop loss value
            'exit_date': exit_date,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'exit_volume': exit_volume,        # Add exit volume
            'profit': profit
        })

        i = j
        continue

    i += 1

#calculate the total profit
total_profit = sum(trade['profit'] for trade in trade_list)
print(f"Total Profit: {total_profit}")

#I want the winrate
win_count = sum(1 for trade in trade_list if trade['profit'] > 0)
win_rate = win_count / len(trade_list) if trade_list else 0
print(f"Win Rate: {win_rate:.2%}")
# Convert trade list to DataFrame and save
trades_df = pd.DataFrame(trade_list)
trades_df.to_csv("tesla_RR2.5.csv", index=False)


# Optional: save result to CSV
#df.to_csv("alarms.csv", index=False)
