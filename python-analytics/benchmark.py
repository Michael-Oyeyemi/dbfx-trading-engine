import requests
import time
import concurrent.futures
import statistics
import sys

# --- Configuration ---
JAVA_BACKEND_URL = "http://localhost:8080/api/trade/execute"
JAVA_SETUP_URL = "http://localhost:8080/api/portfolio/setup"
TOTAL_REQUESTS = 2000
CONCURRENT_THREADS = 20

def setup_benchmark_environment():
    print("Seeding Java database with a dummy Portfolio")
    setup_payload = {
        "portfolios": [
            {
                "id": 1,
                "username": "Stress_Test_Bot",
                "starting_cash": 1000000.0,
                "starting_positions": [{"ticker": "AAPL", "quantity": 50000}]
            }
        ]
    }
    try:
        response = requests.post(JAVA_SETUP_URL, json=setup_payload)
        if response.status_code == 200:
            print("Database seeded.n")
        else:
            print(f"Failed to seed: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Could not connect to Java backend, make sure server is running.")
        sys.exit(1)

def send_dummy_trade(order_id):
    payload = {
        "portfolioId": 1,
        "ticker": "AAPL",
        "side": "BUY" if order_id % 2 == 0 else "SELL", 
        "price": 150.00 + (order_id % 10),
        "quantity": 10
    }
    
    start_time = time.perf_counter()
    try:
        response = requests.post(JAVA_BACKEND_URL, json=payload, timeout=2)
        status = response.status_code
    except requests.exceptions.RequestException:
        status = 500
    end_time = time.perf_counter()
    
    return (end_time - start_time) * 1000, status

def run_stress_test():
    print("Java Backend Stress Test")
    
    setup_benchmark_environment()
    
    print(f"Firing {TOTAL_REQUESTS} concurrent orders across {CONCURRENT_THREADS} threads...")
    
    latencies = []
    success_count = 0
    failed_count = 0
    
    start_time_global = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_THREADS) as executor:
        results = list(executor.map(send_dummy_trade, range(TOTAL_REQUESTS)))
        
    end_time_global = time.perf_counter()
    
    for latency, status in results:
        if status in (200, 202):
            success_count += 1
            latencies.append(latency)
        else:
            failed_count += 1
            
    total_time = end_time_global - start_time_global
    throughput = TOTAL_REQUESTS / total_time
    
    print("\nSYSTEM THROUGHPUT")
    print(f"Total Requests:      {TOTAL_REQUESTS}")
    print(f"Successful Trades:   {success_count}")
    print(f"Failed Trades:       {failed_count}")
    print(f"Total Time Taken:    {total_time:.2f} seconds")
    print(f"Throughput (OPS):    {throughput:.2f} orders/sec")
    
    if latencies:
        print("\nLATENCY METRICS")
        print(f"Average Latency:     {statistics.mean(latencies):.2f} ms")
        print(f"Median Latency:      {statistics.median(latencies):.2f} ms")
        print(f"Min Latency:         {min(latencies):.2f} ms")
        print(f"Max Latency:         {max(latencies):.2f} ms")

if __name__ == "__main__":
    run_stress_test()