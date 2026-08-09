package com.michael.dbxf.dto;

import com.michael.dbxf.model.Position;
import java.math.BigDecimal;
import java.util.List;

public record PortfolioSummary(
        Long id,
        String username,
        BigDecimal cashBalance,
        List<Position> positions
) {}