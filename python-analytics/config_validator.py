import json
import sys
import yfinance as yf

VALID_PERIODS = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
VALID_INTERVALS = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
VALID_STRATEGIES = ["SMA_CROSSOVER", "RSI", "BOLLINGER_BANDS"]

def abort_simulation(error_message):
    print(f"\nAn error occured: {error_message}")
    print("Simulation aborted.\n")
    sys.exit(1)

def _validate_types_and_structure(config):
    print("Checking configuration structure and data types")
    
    if "data_ingestion" not in config or "portfolios" not in config:
        abort_simulation("Missing top-level keys. 'data_ingestion' and 'portfolios' are required.")
        
    ingestion = config["data_ingestion"]
    if not isinstance(ingestion.get("tickers"), list) or len(ingestion["tickers"]) == 0:
        abort_simulation("'tickers' must be a non-empty list of strings.")
    
    if not isinstance(ingestion.get("period"), str) or not isinstance(ingestion.get("interval"), str):
        abort_simulation("'period' and 'interval' must be strings.")

    for portfolio in config["portfolios"]:
        if not isinstance(portfolio.get("id"), int):
            abort_simulation(f"Portfolio ID must be an integer. Found: {portfolio.get('id')}")
        if not isinstance(portfolio.get("starting_cash"), (int, float)):
            abort_simulation(f"Portfolio {portfolio.get('id')} 'starting_cash' must be a number.")
        if not isinstance(portfolio.get("strategy"), dict):
            abort_simulation(f"Portfolio {portfolio.get('id')} is missing a valid 'strategy' block.")

def _validate_time_parameters(config):
    print("Verifying time periods and intervals")
    period = config["data_ingestion"]["period"]
    interval = config["data_ingestion"]["interval"]
    
    if period not in VALID_PERIODS:
        abort_simulation(f"Invalid time period '{period}'. Accepted values are: {VALID_PERIODS}")
        
    if interval not in VALID_INTERVALS:
        abort_simulation(f"Invalid interval '{interval}'. Accepted values are: {VALID_INTERVALS}")

def _validate_market_data(config):
    print("Pinging Yahoo Finance for data integrity")
    tickers = config["data_ingestion"]["tickers"]
    period = config["data_ingestion"]["period"]
    interval = config["data_ingestion"]["interval"]
    
    for ticker_symbol in tickers:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            abort_simulation(f"yfinance returned 0 rows for ticker '{ticker_symbol}'. Please verify the symbol is correct and active.")
    print(f"Successfully verified {len(tickers)} tickers")

def _validate_portfolios(config):
    """Ensures portfolio strategies are valid and they only trade approved tickers."""
    print("Cross-referencing portfolio assignments")
    approved_tickers = config["data_ingestion"]["tickers"]
    
    for portfolio in config["portfolios"]:
        pid = portfolio["id"]
        
        strategy_type = portfolio["strategy"].get("type")
        if strategy_type not in VALID_STRATEGIES:
            abort_simulation(f"Portfolio {pid} has invalid strategy '{strategy_type}'. Accepted: {VALID_STRATEGIES}")
            
        for position in portfolio.get("starting_positions", []):
            pos_ticker = position.get("ticker")
            if pos_ticker not in approved_tickers:
                abort_simulation(f"Portfolio {pid} requests starting shares in '{pos_ticker}', but it is not in the data_ingestion list.")

def load_and_validate_config(filepath):
    config = None
    try:
        with open(filepath, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        abort_simulation(f"Could not find configuration file at '{filepath}'.")
    except json.JSONDecodeError as e:
        abort_simulation(f"Invalid JSON syntax in '{filepath}': {e}")

    # Run the validation gauntlet
    _validate_types_and_structure(config)
    _validate_time_parameters(config)
    _validate_market_data(config)
    _validate_portfolios(config)
    
    print("\nConfiguration passed all validation checks.\n")
    return config

if __name__ == "__main__":
    load_and_validate_config("config.json") 