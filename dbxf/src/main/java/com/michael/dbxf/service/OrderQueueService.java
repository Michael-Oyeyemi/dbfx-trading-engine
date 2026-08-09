package com.michael.dbxf.service;

import com.michael.dbxf.dto.TradeRequest;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;

@Service
public class OrderQueueService {

    private final LinkedBlockingQueue<TradeRequest> orderQueue = new LinkedBlockingQueue<>();

    // Inject the OrderBook instead of the TradeService
    private final OrderBookService orderBookService;

    private final ExecutorService consumerThread = Executors.newSingleThreadExecutor();

    public OrderQueueService(OrderBookService orderBookService) {
        this.orderBookService = orderBookService;
    }

    public void enqueueOrder(TradeRequest request) {
        orderQueue.offer(request);
    }

    @PostConstruct
    public void startConsumer() {
        consumerThread.submit(() -> {
            while (true) {
                try {
                    // Pull from the queue
                    TradeRequest request = orderQueue.take();

                    // Route to the in-memory order book for matching
                    orderBookService.addOrderToBook(request);

                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        });
    }
}