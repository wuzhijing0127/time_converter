import pandas as pd

def clean_datetime(file_path):
    """
    Cleans the datetime column in the CSV file by splitting it into date and time columns
    and removing timezone information.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pandas.DataFrame: DataFrame with cleaned date and time columns
    """
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Create temporary column names for the split
    temp_cols = df['date'].str.split(' ', expand=True)
    
    # Extract date and time (excluding timezone)
    df['date'] = temp_cols[0]
    df['time'] = temp_cols[1].str.split('-').str[0]  # Split on '-' and take first part
    
    # Reorder columns to put date and time first
    columns_order = ['date', 'time', 'open', 'high', 'low', 'close', 'volume', 'average', 'barCount']
    df = df[columns_order]
    
    return df
