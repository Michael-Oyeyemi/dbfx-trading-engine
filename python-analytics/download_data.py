import yfinance as yf
import pandas as pd

def fetch_market_data(config):
    """
    Ingests the master JSON config and downloads the required market data dynamically.
    Returns a dictionary mapping the ticker symbol to its downloaded CSV filename.
    """
    print("\nInitializing dynamic data download pipeline")
    
    ingestion_config = config.get("data_ingestion", {})
    tickers = ingestion_config.get("tickers", [])
    period = ingestion_config.get("period", "1y")
    interval = ingestion_config.get("interval", "1d")
    
    downloaded_files = {}

    for ticker_symbol in tickers:
        print(f"Fetching {period} of data for {ticker_symbol} at {interval} intervals...")
        
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period, interval=interval)
        
        df.reset_index(inplace=True)
        
        if 'Datetime' in df.columns:
            df.rename(columns={'Datetime': 'Date'}, inplace=True)
            
        df['Date'] = df['Date'].dt.tz_localize(None)
        clean_df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        filename = f"{ticker_symbol}_historical.csv"
        clean_df.to_csv(filename, index=False)
        
        downloaded_files[ticker_symbol] = filename
        print(f" -> Saved {len(clean_df)} rows to {filename}")
        
    print("All requested market data successfully downloaded.\n")
    return downloaded_files

if __name__ == "__main__":
    mock_config = {
        "data_ingestion": {
            "tickers": ["AAPL"],
            "period": "1mo",
            "interval": "1d"
        }
    }
    fetch_market_data(mock_config)