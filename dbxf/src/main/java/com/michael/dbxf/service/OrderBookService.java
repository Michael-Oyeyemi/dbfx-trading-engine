package com.michael.dbxf.service;

import com.michael.dbxf.dto.TradeRequest;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ConcurrentSkipListMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
public class OrderBookService {

    private final TradeService tradeService;

    // BUY Book: Sorted highest price to lowest price (Collections.reverseOrder)
    private final ConcurrentSkipListMap<BigDecimal, Queue<TradeRequest>> buyBook =
            new ConcurrentSkipListMap<>(Collections.reverseOrder());

    // SELL Book: Sorted lowest price to highest price (Default natural ordering)
    private final ConcurrentSkipListMap<BigDecimal, Queue<TradeRequest>> sellBook =
            new ConcurrentSkipListMap<>();

    private final ExecutorService matchingEngineThread = Executors.newSingleThreadExecutor();

    public OrderBookService(TradeService tradeService) {
        this.tradeService = tradeService;
    }

    // 1. Add incoming orders to the correct book
    public void addOrderToBook(TradeRequest request) {
        if ("BUY".equalsIgnoreCase(request.side())) {
            buyBook.computeIfAbsent(request.price(), k -> new ConcurrentLinkedQueue<>()).add(request);
        } else if ("SELL".equalsIgnoreCase(request.side())) {
            sellBook.computeIfAbsent(request.price(), k -> new ConcurrentLinkedQueue<>()).add(request);
        }
    }

    // 2. The Matching Engine: Runs constantly in the background
    @PostConstruct
    public void startMatchingEngine() {
        matchingEngineThread.submit(() -> {
            while (true) {
                try {
                    matchOrders();
                    // Sleep for 10 milliseconds to prevent maxing out the CPU
                    Thread.sleep(10);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        });
    }

    private void matchOrders() {
        // If either book is empty, no match can be made
        if (buyBook.isEmpty() || sellBook.isEmpty()) return;

        // Look at the top prices (Highest Buy vs Lowest Sell)
        BigDecimal topBuyPrice = buyBook.firstKey();
        BigDecimal topSellPrice = sellBook.firstKey();

        // If the buyer is willing to pay equal to or more than the seller's asking price
        if (topBuyPrice.compareTo(topSellPrice) >= 0) {

            Queue<TradeRequest> buyQueue = buyBook.get(topBuyPrice);
            Queue<TradeRequest> sellQueue = sellBook.get(topSellPrice);

            TradeRequest buyer = buyQueue.poll();
            TradeRequest seller = sellQueue.poll();

            if (buyer != null && seller != null) {
                System.out.println("MATCH FOUND! Buyer: " + buyer.portfolioId() + " | Seller: " + seller.portfolioId());

                // Execute the trade securely in the database using the Retryable TradeService
                try {
                    tradeService.executeTrade(buyer.portfolioId(), buyer.ticker(), buyer.side(), topBuyPrice, buyer.quantity());
                    tradeService.executeTrade(seller.portfolioId(), seller.ticker(), seller.side(), topSellPrice, seller.quantity());
                } catch (Exception e) {
                    System.err.println("Trade Execution Failed after retries: " + e.getMessage());
                }
            }

            // Clean up empty price levels so the map doesn't leak memory
            if (buyQueue != null && buyQueue.isEmpty()) buyBook.remove(topBuyPrice);
            if (sellQueue != null && sellQueue.isEmpty()) sellBook.remove(topSellPrice);
        }
    }
}