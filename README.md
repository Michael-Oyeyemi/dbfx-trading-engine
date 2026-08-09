# DBXF: Distributed Backtesting & Order Execution Framework

A hybrid distributed trading system engineered to stress-test quantitative trading strategies across multi-asset portfolios. 

This project utilizes a microservice architecture, splitting the high-concurrency order execution engine (Java/Spring Boot) from the quantitative analytics and data ingestion pipeline (Python).

---

## System Architecture

The framework is decoupled into two primary components communicating via RESTful APIs:

*   **Java Backend (The Exchange/Broker):** Built with Spring Boot, this high-throughput backend handles order matching, portfolio seeding, and balance management. It leverages advanced concurrency patterns including thread-safe producer-consumer queues (`LinkedBlockingQueue`), in-memory order matching engines (`ConcurrentSkipListMap`), and optimistic locking to prevent race conditions during high-frequency signal streaming.
*   **Python Analytics (The Quant/Orchestrator):** A dynamic orchestration service that reads from a central JSON blueprint. It ingests historical multi-asset data via `yfinance`, calculates technical indicators (SMA, RSI, Bollinger Bands) using `pandas`, and streams asynchronous buy/sell signals to the Java backend. 

---

## Features

*   **Fail-Fast Configuration Pipeline:** A strict validation gatekeeper that sanitizes requested tickers, time periods, and JSON structures before executing data ingestion.
*   **Dynamic Database Seeding:** The Python orchestrator dynamically commands the Java backend to wipe and seed the in-memory H2 database with the exact portfolios and cash balances required for the simulation.
*   **Concurrent Multi-Strategy Execution:** Simulates multiple trading bots simultaneously, evaluating discrete mathematical strategies against the same asset data.
*   **Automated Tear Sheets:** Utilizes `matplotlib` in non-blocking mode to generate multi-panel equity curves and trade signal visualizations for true Net Asset Value (NAV) tracking.

---

## Prerequisites

To run this simulation locally, you will need:
*   Java 17 or higher
*   Maven
*   Python 3.10 or higher

---

## Installation & Boot Sequence

Because this is a distributed system, you must start the Java backend before launching the Python quantitative simulation.

### Step 1: Start the Java Execution Engine
Open a terminal, navigate to the Java project directory, and boot the Spring application.

```bash
cd dbxf
mvn spring-boot:run
```
The backend will initialize an empty in-memory H2 database and bind to `localhost:8080`.

### Step 2: Start the Python Analytics Orchestrator
Open a **second terminal**, navigate to the Python project directory, install the dependencies, and run the simulation.

```bash
cd python-analytics

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install quantitative libraries
pip install -r requirements.txt

# Execute the simulation
python backtester.py
```

---

## Configuration Blueprint

The entire simulation is controlled by the `config.json` file located in the Python directory. You can modify the tickers, time periods, and mathematical strategy parameters here without altering any source code. 

```json
{
  "simulation_name": "Tech_Stock_Stress_Test",
  "data_ingestion": {
    "tickers": ["AAPL", "NVDA", "TSLA"],
    "period": "2y",
    "interval": "1d"
  },
  "portfolios": [
    {
      "id": 1,
      "username": "SMA_Fast_Bot",
      "starting_cash": 100000.0,
      "strategy": {
        "type": "SMA_CROSSOVER",
        "parameters": {
          "short_window": 5,
          "long_window": 20
        }
      }
    }
  ]
}
```

---

## Output Examples

Upon completion, the Python service fetches the final validated cash and inventory balances from the Java database. It prints a comprehensive Net Asset Value (NAV) breakdown to the console and generates distinct interactive charts for each evaluated asset.
