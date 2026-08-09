import pandas as pd
import requests
import time
import sys
import matplotlib.pyplot as plt
import config_validator
import download_data

# --- Configuration Constants ---
JAVA_BACKEND_URL = "http://localhost:8080/api/trade/execute"
JAVA_PORTFOLIO_URL = "http://localhost:8080/api/portfolio"
JAVA_SETUP_URL = "http://localhost:8080/api/portfolio/setup"

# ==========================================
# API NETWORKING & BACKEND INTEGRATION
# ==========================================

def send_trade_signal(portfolio_id, ticker, side, price, quantity):
    payload = {
        "portfolioId": portfolio_id,
        "ticker": ticker,
        "side": side,
        "price": float(price),
        "quantity": int(quantity)
    }
    try:
        response = requests.post(JAVA_BACKEND_URL, json=payload)
        if response.status_code != 202:
            print(f"[ERROR] Rejected: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        pass

def fetch_portfolio_summary(portfolio_id):
    try:
        res = requests.get(f"{JAVA_PORTFOLIO_URL}/{portfolio_id}")
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.ConnectionError:
        pass
    return None

def setup_java_backend(portfolios):
    print("\n[SETUP] Dynamically seeding Java Backend Database...")
    try:
        response = requests.post(JAVA_SETUP_URL, json={"portfolios": portfolios})
        if response.status_code == 200:
            print("[SUCCESS] Java backend successfully seeded with JSON configuration.\n")
        else:
            print(f"[ERROR] Backend setup failed: {response.status_code} - {response.text}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("[CRITICAL] Could not connect to Java backend. Is Spring Boot running?")
        sys.exit(1)

# ==========================================
# MODULAR STRATEGY ENGINE
# ==========================================

def apply_strategy_indicators(df, portfolios):
    """
    Dynamically applies technical indicators to the DataFrame based on the JSON config.
    """
    for p in portfolios:
        pid = p["id"]
        strat = p["strategy"]
        stype = strat["type"]
        params = strat["parameters"]

        if stype == "SMA_CROSSOVER":
            df[f'P{pid}_SMA_Short'] = df['Close'].rolling(window=params["short_window"]).mean()
            df[f'P{pid}_SMA_Long'] = df['Close'].rolling(window=params["long_window"]).mean()

        elif stype == "RSI":
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=params["time_period"]).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=params["time_period"]).mean()
            rs = gain / loss
            df[f'P{pid}_RSI'] = 100 - (100 / (1 + rs))

        elif stype == "BOLLINGER_BANDS":
            window = params["moving_average_window"]
            std_mult = params["standard_deviation_multiplier"]
            df[f'P{pid}_BB_SMA'] = df['Close'].rolling(window=window).mean()
            std = df['Close'].rolling(window=window).std()
            df[f'P{pid}_BB_Upper'] = df[f'P{pid}_BB_SMA'] + (std * std_mult)
            df[f'P{pid}_BB_Lower'] = df[f'P{pid}_BB_SMA'] - (std * std_mult)

    return df

def evaluate_trade_signal(prev, current, portfolio_config):
    """
    Evaluates a single day's price action against the defined strategy rules.
    Returns 'BUY', 'SELL', or None.
    """
    pid = portfolio_config["id"]
    stype = portfolio_config["strategy"]["type"]
    params = portfolio_config["strategy"]["parameters"]

    if stype == "SMA_CROSSOVER":
        short_col = f'P{pid}_SMA_Short'
        long_col = f'P{pid}_SMA_Long'
        if prev[short_col] <= prev[long_col] and current[short_col] > current[long_col]:
            return "BUY"
        elif prev[short_col] >= prev[long_col] and current[short_col] < current[long_col]:
            return "SELL"

    elif stype == "RSI":
        rsi_col = f'P{pid}_RSI'
        oversold = params["oversold_threshold"]
        overbought = params["overbought_threshold"]
        if prev[rsi_col] <= oversold and current[rsi_col] > oversold:
            return "BUY"
        elif prev[rsi_col] >= overbought and current[rsi_col] < overbought:
            return "SELL"

    elif stype == "BOLLINGER_BANDS":
        lower_col = f'P{pid}_BB_Lower'
        upper_col = f'P{pid}_BB_Upper'
        if prev['Close'] >= prev[lower_col] and current['Close'] < current[lower_col]:
            return "BUY"
        elif prev['Close'] <= prev[upper_col] and current['Close'] > current[upper_col]:
            return "SELL"

    return None

# ==========================================
# VISUALIZATION & CORE LOOP
# ==========================================

def plot_dynamic_results(df, signals_dict, nav_history_dict, ticker, portfolios):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
    
    # --- Top Panel: Stock Price & Signals ---
    ax1.plot(df['Date'], df['Close'], label=f'{ticker} Price', color='gray', alpha=0.5, linewidth=1.5)
    
    colors = ['blue', 'orange', 'purple', 'green']
    markers = [('^', 'v', 'green', 'red'), ('^', 'v', 'cyan', 'magenta'), ('^', 'v', 'black', 'black'), ('^', 'v', 'lime', 'darkred')]
    
    for idx, p in enumerate(portfolios):
        pid = p["id"]
        color = colors[idx % len(colors)]
        stype = p["strategy"]["type"]
        
        # Only plot overlay lines if they are price-scaled (skip RSI 0-100 overlay on $400 price axis)
        if stype == "SMA_CROSSOVER":
            sw = p["strategy"]["parameters"]["short_window"]
            lw = p["strategy"]["parameters"]["long_window"]
            ax1.plot(df['Date'], df[f'P{pid}_SMA_Short'], label=f'P{pid} SMA ({sw})', color=color, linestyle=':', alpha=0.4)
            ax1.plot(df['Date'], df[f'P{pid}_SMA_Long'], label=f'P{pid} SMA ({lw})', color=color, linestyle='-', alpha=0.4)
        elif stype == "BOLLINGER_BANDS":
            ax1.plot(df['Date'], df[f'P{pid}_BB_Upper'], label=f'P{pid} BB Upper', color=color, linestyle='--', alpha=0.4)
            ax1.plot(df['Date'], df[f'P{pid}_BB_Lower'], label=f'P{pid} BB Lower', color=color, linestyle='--', alpha=0.4)

        m_buy, m_sell, c_buy, c_sell = markers[idx % len(markers)]
        for date, price, side in signals_dict[pid]:
            ax1.scatter(date, price, color=c_buy if side == 'BUY' else c_sell, marker=m_buy if side == 'BUY' else m_sell, s=100)

    ax1.set_title(f"DBXF Dynamic Strategy Clash on {ticker}", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Price ($)", fontsize=12)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # --- Bottom Panel: Portfolio Value (NAV) Over Time ---
    for idx, p in enumerate(portfolios):
        pid = p["id"]
        color = colors[idx % len(colors)]
        ax2.plot(df['Date'], nav_history_dict[pid], label=f'Portfolio {pid} ({p["username"]}) NAV', color=color, linewidth=2)
    
    ax2.set_title("Equity Curve (Net Asset Value)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Date", fontsize=12)
    ax2.set_ylabel("Total Value ($)", fontsize=12)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.show(block=False)

def run_dynamic_simulation(config_filepath="config.json"):
    print("==================================================")
    print("      DBXF DYNAMIC MULTI-ASSET SIMULATION         ")
    print("==================================================")

    config = config_validator.load_and_validate_config(config_filepath)
    portfolios = config["portfolios"]

    downloaded_files = download_data.fetch_market_data(config)
    setup_java_backend(portfolios)

    global_initial_prices = {}
    global_latest_prices = {}

    for ticker, filepath in downloaded_files.items():
        print(f"\n[STREAMING] Loading {ticker} data...")
        df = pd.read_csv(filepath)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
        
        global_initial_prices[ticker] = df.iloc[0]['Close']
        signals_dict = {p["id"]: [] for p in portfolios}
        nav_history_dict = {p["id"]: [] for p in portfolios}
        
        internal_tracking = {}
        for p in portfolios:
            start_cash = p.get("starting_cash", 100000.0)
            start_shares = next((pos["quantity"] for pos in p.get("starting_positions", []) if pos["ticker"] == ticker), 0)
            internal_tracking[p["id"]] = {"cash": start_cash, "shares": start_shares}

        # MODULAR CALL: Apply all technical indicators upfront
        df = apply_strategy_indicators(df, portfolios)
        latest_price = 0.0

        print(f"Streaming high-frequency signals for {ticker} to Java backend...")
        for i in range(len(df)):
            if i == 0: 
                for p in portfolios:
                    pid = p["id"]
                    nav_history_dict[pid].append(internal_tracking[pid]["cash"] + (internal_tracking[pid]["shares"] * df.iloc[i]['Close']))
                continue
                
            current = df.iloc[i]
            prev = df.iloc[i - 1]
            price = current['Close']
            date = current['Date']
            latest_price = price

            for p in portfolios:
                pid = p["id"]
                
                # MODULAR CALL: Evaluate strategy logic
                signal = evaluate_trade_signal(prev, current, p)
                
                if signal == "BUY":
                    send_trade_signal(pid, ticker, "BUY", price, 10)
                    signals_dict[pid].append((date, price, 'BUY'))
                    internal_tracking[pid]["cash"] -= price * 10
                    internal_tracking[pid]["shares"] += 10
                
                elif signal == "SELL":
                    send_trade_signal(pid, ticker, "SELL", price, 10)
                    signals_dict[pid].append((date, price, 'SELL'))
                    internal_tracking[pid]["cash"] += price * 10
                    internal_tracking[pid]["shares"] -= 10

                nav_history_dict[pid].append(internal_tracking[pid]["cash"] + (internal_tracking[pid]["shares"] * price))
            
            time.sleep(0.005)

        global_latest_prices[ticker] = latest_price
        time.sleep(1.0) 

        print("\n==================================================")
        print(f"           FINAL VALUATIONS (NAV) - {ticker}      ")
        print("==================================================")
        
        for p in portfolios:
            pid = p["id"]
            summary = fetch_portfolio_summary(pid)
            if not summary: continue
            
            initial_nav = p.get("starting_cash", 100000.0) + (next((pos["quantity"] for pos in p.get("starting_positions", []) if pos["ticker"] == ticker), 0) * df.iloc[0]['Close'])
            
            cash = float(summary.get("cashBalance", 0.0))
            positions = summary.get("positions", [])
            holdings_value = 0.0
            
            print(f"\n📊 Portfolio #{pid} ({summary.get('username')})")
            for pos in positions:
                sym, qty = pos.get("ticker"), pos.get("quantity", 0)
                if sym == ticker:
                    val = qty * latest_price
                    holdings_value += val
                    print(f"   Holdings: {qty} {sym} @ ${latest_price:,.2f} = ${val:,.2f}")
                
            total_nav = cash + holdings_value
            print(f"   Total NAV (for {ticker} context): ${total_nav:,.2f}")

        print(f"\n[VISUALIZATION] Launching performance chart for {ticker}...")
        plot_dynamic_results(df, signals_dict, nav_history_dict, ticker, portfolios)

    # --- GLOBAL PORTFOLIO PERFORMANCE ---
    print("\n==================================================")
    print("  🌍 FINAL GLOBAL PORTFOLIO PERFORMANCE (ALL ASSETS)")
    print("==================================================")
    
    for p in portfolios:
        pid = p["id"]
        summary = fetch_portfolio_summary(pid)
        if not summary: continue
        
        initial_cash = p.get("starting_cash", 100000.0)
        initial_holdings_value = sum(pos.get("quantity", 0) * global_initial_prices.get(pos.get("ticker"), 0) for pos in p.get("starting_positions", []))
        global_initial_nav = initial_cash + initial_holdings_value

        final_cash = float(summary.get("cashBalance", 0.0))
        positions = summary.get("positions", [])
        final_holdings_value = 0.0
        
        print(f"\n📊 Portfolio #{pid} ({summary.get('username')})")
        print(f"   Final Available Cash: ${final_cash:,.2f}")
        
        for pos in positions:
            sym, qty = pos.get("ticker"), pos.get("quantity", 0)
            if sym in global_latest_prices:
                val = qty * global_latest_prices[sym]
                final_holdings_value += val
                print(f"   Final Holdings: {qty} {sym} @ ${global_latest_prices[sym]:,.2f} = ${val:,.2f}")
            
        global_final_nav = final_cash + final_holdings_value
        print(f"   ----------------------------------------")
        print(f"   TOTAL GLOBAL NAV:     ${global_final_nav:,.2f}")
        
        if global_initial_nav > 0:
            net_return = ((global_final_nav - global_initial_nav) / global_initial_nav) * 100.0
            print(f"   OVERALL NET RETURN:   {net_return:+.2f}%")

    plt.show()

if __name__ == "__main__":
    run_dynamic_simulation()