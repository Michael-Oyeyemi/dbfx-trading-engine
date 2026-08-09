package com.michael.dbxf.controller;

import com.michael.dbxf.dto.PortfolioSummary;
import com.michael.dbxf.model.Portfolio;
import com.michael.dbxf.repository.PortfolioRepository;
import com.michael.dbxf.repository.PositionRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/portfolio")
public class PortfolioController {

    private final PortfolioRepository portfolioRepository;
    private final PositionRepository positionRepository;

    public PortfolioController(PortfolioRepository portfolioRepository, PositionRepository positionRepository) {
        this.portfolioRepository = portfolioRepository;
        this.positionRepository = positionRepository;
    }

    @GetMapping("/{id}")
    public ResponseEntity<PortfolioSummary> getPortfolioSummary(@PathVariable Long id) {
        Portfolio portfolio = portfolioRepository.findById(id).orElse(null);
        if (portfolio == null) {
            return ResponseEntity.notFound().build();
        }

        var positions = positionRepository.findByPortfolioId(id);

        PortfolioSummary summary = new PortfolioSummary(
                portfolio.getId(),
                portfolio.getUsername(),
                portfolio.getBalance(),
                positions
        );

        return ResponseEntity.ok(summary);
    }
}