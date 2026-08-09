package com.michael.dbxf.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.util.List;

public record PortfolioSetupDTO(
        Long id,
        String username,
        @JsonProperty("starting_cash") BigDecimal startingCash,
        @JsonProperty("starting_positions") List<PositionSetupDTO> startingPositions
) {}