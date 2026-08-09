package com.michael.dbxf.service;

import com.michael.dbxf.dto.SetupRequest;
import com.michael.dbxf.model.Portfolio;
import com.michael.dbxf.model.Position;
import com.michael.dbxf.repository.OrderRepository;
import com.michael.dbxf.repository.PortfolioRepository;
import com.michael.dbxf.repository.PositionRepository;
import jakarta.persistence.EntityManager;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
public class SetupService {

    private final PortfolioRepository portfolioRepository;
    private final PositionRepository positionRepository;
    private final OrderRepository orderRepository;
    private final EntityManager entityManager;

    public SetupService(PortfolioRepository portfolioRepository,
                        PositionRepository positionRepository,
                        OrderRepository orderRepository,
                        EntityManager entityManager) {
        this.portfolioRepository = portfolioRepository;
        this.positionRepository = positionRepository;
        this.orderRepository = orderRepository;
        this.entityManager = entityManager;
    }

    @Transactional
    public void initializeEnvironment(SetupRequest request) {
        // 1. Wipe the database
        orderRepository.deleteAll();
        positionRepository.deleteAll();
        portfolioRepository.deleteAll();

        // 2. Reset the ID auto-increment counters back to 1
        entityManager.createNativeQuery("ALTER TABLE portfolio ALTER COLUMN id RESTART WITH 1").executeUpdate();
        entityManager.createNativeQuery("ALTER TABLE portfolio_position ALTER COLUMN id RESTART WITH 1").executeUpdate();
        entityManager.createNativeQuery("ALTER TABLE trade_order ALTER COLUMN id RESTART WITH 1").executeUpdate();

        if (request.portfolios() == null) return;

        List<Position> allPositions = new ArrayList<>();

        // 3. Dynamically build the new state from the JSON configuration
        for (var pDto : request.portfolios()) {
            Portfolio portfolio = new Portfolio();
            portfolio.setUsername(pDto.username());
            portfolio.setBalance(pDto.startingCash());

            // Save immediately to generate the primary key ID
            portfolio = portfolioRepository.save(portfolio);

            if (pDto.startingPositions() != null) {
                for (var posDto : pDto.startingPositions()) {
                    Position position = new Position();
                    position.setPortfolioId(portfolio.getId());
                    position.setTicker(posDto.ticker().toUpperCase());
                    position.setQuantity(posDto.quantity());
                    allPositions.add(position);
                }
            }
        }

        // Save all associated starting inventory
        positionRepository.saveAll(allPositions);
    }
}