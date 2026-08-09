package com.michael.dbxf.dto;

import java.util.List;

public record SetupRequest(
        List<PortfolioSetupDTO> portfolios
) {}