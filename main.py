import data_cleaning
import timeframe_converter
import pandas as pd
import os
import argparse

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Process stock market data with custom timeframes')
    
    # Add arguments
    parser.add_argument('file_path', type=str, help='Path to the input CSV file')
    parser.add_argument('timeframe', type=int, help='Timeframe in minutes for conversion')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Clean the data first
    df = data_cleaning.clean_datetime(args.file_path)
    
    # Convert timeframe
    converted_df = timeframe_converter.convert_timeframe(df, args.timeframe)
    
    # Create output filename
    output_filename = f'{args.timeframe}min.csv'
    converted_df.to_csv(output_filename, index=False)
    print(f"Processing complete. Output saved to {output_filename}")

if __name__ == "__main__":
    main()

