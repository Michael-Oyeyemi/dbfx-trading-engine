package com.michael.dbxf.dto;

import java.math.BigDecimal;

public record TradeRequest(
        Long portfolioId,
        String ticker,
        String side,
        BigDecimal price,
        Integer quantity
) {}