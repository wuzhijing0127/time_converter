import pandas as pd
import numpy as np
import talib

#we enter the trade only if we got a buy signal

def supertrend(df, atr_periods=15, multiplier=1):
    """
    Calculate Supertrend indicator and buy/sell signals.
    Expects columns: 'High', 'Low', 'Close'
    Returns a DataFrame with columns: 'supertrend', 'final_upperband', 'final_lowerband', 'signal'
    """
    df = df.copy()
    # True Range
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - df['Close'].shift(1)).abs(),
        (df['Low'] - df['Close'].shift(1)).abs()
    ], axis=1).max(axis=1)
    tr.iloc[0] = 0

    # ATR (EMA smoothing)
    weight = 2 / (atr_periods + 1)
    atr = pd.Series(index=tr.index, dtype=float)
    for i in range(len(tr)):
        if i < atr_periods:
            continue
        elif i == atr_periods:
            atr.iloc[i] = tr.iloc[i-atr_periods+1:i+1].mean()
        else:
            atr.iloc[i] = weight * tr.iloc[i] + (1 - weight) * atr.iloc[i-1]

    # Bands
    hl2 = (df['High'] + df['Low']) / 2
    basic_upperband = hl2 + multiplier * atr
    basic_lowerband = hl2 - multiplier * atr

    # Final bands
    final_upperband = pd.Series(index=df.index, dtype=float)
    final_lowerband = pd.Series(index=df.index, dtype=float)
    for i in range(len(df)):
        if i < atr_periods:
            continue
        if i == atr_periods:
            final_upperband.iloc[i] = basic_upperband.iloc[i]
            final_lowerband.iloc[i] = basic_lowerband.iloc[i]
        else:
            prev_close = df['Close'].iloc[i-1]
            prev_final_upper = final_upperband.iloc[i-1]
            prev_final_lower = final_lowerband.iloc[i-1]
            if basic_upperband.iloc[i] < prev_final_upper or prev_close > prev_final_upper:
                final_upperband.iloc[i] = basic_upperband.iloc[i]
            else:
                final_upperband.iloc[i] = prev_final_upper
            if basic_lowerband.iloc[i] > prev_final_lower or prev_close < prev_final_lower:
                final_lowerband.iloc[i] = basic_lowerband.iloc[i]
            else:
                final_lowerband.iloc[i] = prev_final_lower

    # Supertrend and signals
    supertrend = pd.Series(index=df.index, dtype=float)
    in_uptrend = True
    signal = pd.Series(0, index=df.index, dtype=int)
    for i in range(len(df)):
        if i < atr_periods:
            supertrend.iloc[i] = np.nan
            continue
        if i == atr_periods:
            supertrend.iloc[i] = final_lowerband.iloc[i]
            in_uptrend = True
        else:
            prev_supertrend = supertrend.iloc[i-1]
            curr_close = df['Close'].iloc[i]
            prev_final_upper = final_upperband.iloc[i-1]
            prev_final_lower = final_lowerband.iloc[i-1]
            if prev_supertrend == prev_final_upper:
                if curr_close <= final_upperband.iloc[i]:
                    supertrend.iloc[i] = final_upperband.iloc[i]
                    if in_uptrend:  # switched from uptrend to downtrend
                        signal.iloc[i] = -1  # Sell
                    in_uptrend = False
                else:
                    supertrend.iloc[i] = final_lowerband.iloc[i]
                    if not in_uptrend:  # switched from downtrend to uptrend
                        signal.iloc[i] = 1  # Buy
                    in_uptrend = True
            else:
                if curr_close >= final_lowerband.iloc[i]:
                    supertrend.iloc[i] = final_lowerband.iloc[i]
                    if not in_uptrend:
                        signal.iloc[i] = 1  # Buy
                    in_uptrend = True
                else:
                    supertrend.iloc[i] = final_upperband.iloc[i]
                    if in_uptrend:
                        signal.iloc[i] = -1  # Sell
                    in_uptrend = False

    result = pd.DataFrame({
        'supertrend': supertrend,
        'final_upperband': final_upperband,
        'final_lowerband': final_lowerband,
        'signal': signal
    })
    return result

df =pd.read_excel('spy_1h_new.xlsx', sheet_name='Sheet1', engine='openpyxl')
df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close'}, inplace=True)

#EMA
df['EMA'] = talib.EMA(df['Close'], timeperiod=100)
st = supertrend(df, atr_periods=27, multiplier=3)
df = pd.concat([df, st], axis=1)
# Replace 1 with 'buy', -1 with 'sell', and 0 with empty string in the 'signal' column before saving
df['signal'] = df['signal'].replace({1: 'buy', -1: 'sell', 0: ''})

#save the DataFrame with Supertrend to a new CSV file
df.to_csv('!.csv', index=False)
# Save the DataFrame with Supertrend to a new CSV file


# Calculate trade profits and export detailed trade log
trade_log = []
position = None
entry_price = None
entry_index = None

for i, row in df.iterrows():
    # Enter long only if buy signal and Close > EMA

    if row['signal'] == 'buy' and position != 'long'and row['Close'] > row['EMA']:
        # Close short if open
        if position == 'short':
            profit = entry_price - row['Close']
            trade_log.append({
                'signal': 'sell',
                'enter_date': df.at[entry_index, 'Date'],
                'enter_time': df.at[entry_index, 'Time'],
                'enter_price': entry_price,
                'exit_date': row['Date'],
                'exit_time': row['Time'],
                'exit_price': row['Close'],
                'profit': profit
            })
        # Open long
        position = 'long'
        entry_price = row['Close']
        entry_index = i

    # Enter short only if sell signal and Close < EMA
    
    elif row['signal'] == 'sell' and position != 'short'and row['Close'] < row['EMA']:
        # Close long if open
        if position == 'long':
            profit = row['Close'] - entry_price
            trade_log.append({
                'signal': 'buy',
                'enter_date': df.at[entry_index, 'Date'],
                'enter_time': df.at[entry_index, 'Time'],
                'enter_price': entry_price,
                'exit_date': row['Date'],
                'exit_time': row['Time'],
                'exit_price': row['Close'],
                'profit': profit
            })
        # Open short
        position = 'short'
        entry_price = row['Close']
        entry_index = i

# Optionally, close the last open trade at the last price
if position is not None and entry_index is not None:
    last_row = df.iloc[-1]
    if position == 'long':
        profit = last_row['Close'] - entry_price
        trade_log.append({
            'signal': 'buy',
            'enter_date': df.at[entry_index, 'Date'],
            'enter_time': df.at[entry_index, 'Time'],
            'enter_price': entry_price,
            'exit_date': last_row['Date'],
            'exit_time': last_row['Time'],
            'exit_price': last_row['Close'],
            'profit': profit
        })
    elif position == 'short':
        profit = entry_price - last_row['Close']
        trade_log.append({
            'signal': 'sell',
            'enter_date': df.at[entry_index, 'Date'],
            'enter_time': df.at[entry_index, 'Time'],
            'enter_price': entry_price,
            'exit_date': last_row['Date'],
            'exit_time': last_row['Time'],
            'exit_price': last_row['Close'],
            'profit': profit
        })

#sum up total profit
total_profit = sum(trade['profit'] for trade in trade_log)
#average profit per trade
average_profit = total_profit / len(trade_log) if trade_log else 0
print(f'Average Profit per Trade: {average_profit}')
print(f'Total Profit: {total_profit}')
# Save trade log to CSV
trade_log_df = pd.DataFrame(trade_log)
trade_log_df.to_csv('str_15_3_100.csv', index=False)

#Now I want to optimzie the Supertrend parameters test the atr periods between 3-30 and multiplier between 1-5, use the total profit as the optimization metric.