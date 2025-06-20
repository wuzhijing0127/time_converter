import pandas as pd
from datetime import time

def convert_timeframe(df, timeframe=5):
    # Convert date and time columns to datetime
    df['DateTime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    
    # Function to check if time is within market hours
    def is_market_hours(x):
        t = x.time()
        return (time(9,30) <= t <= time(16,0))
    
    # Filter for market hours
    df = df[df['DateTime'].apply(is_market_hours)]
    
    # Group by date first
    grouped = df.groupby(df['DateTime'].dt.date)
    
    final_df = pd.DataFrame()
    
    for date, group in grouped:
        # Set index for resampling
        group.set_index('DateTime', inplace=True)
        
        # Set the start time to 9:30 for each day
        start_time = pd.Timestamp(date).replace(hour=9, minute=30)
        
        # Resample starting exactly at 9:30
        resampled = group.resample(f'{timeframe}T', origin=start_time).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        final_df = pd.concat([final_df, resampled])
    
    # Reset index to get DateTime back as column
    final_df.reset_index(inplace=True)
    
    # Split DateTime into Date and Time columns
    final_df['Date'] = final_df['DateTime'].dt.date
    final_df['Time'] = final_df['DateTime'].dt.time
    
    # Drop the DateTime column and rows with zero volume
    final_df = final_df.drop(columns=['DateTime'])
    final_df = final_df[final_df['volume'] != 0]
    
    return final_df[['Date', 'Time', 'open', 'high', 'low', 'close', 'volume']]




