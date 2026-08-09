package com.michael.dbxf.controller;

import com.michael.dbxf.dto.TradeRequest;
import com.michael.dbxf.service.OrderQueueService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/trade")
public class TradeController {

    private final OrderQueueService orderQueueService;

    public TradeController(OrderQueueService orderQueueService) {
        this.orderQueueService = orderQueueService;
    }

    @PostMapping("/execute")
    public ResponseEntity<String> executeTrade(@RequestBody TradeRequest request) {
        orderQueueService.enqueueOrder(request);

        // Instantly return an HTTP 202 (Accepted) status to Python
        return ResponseEntity.accepted().body("Order received and queued for processing.");
    }
}