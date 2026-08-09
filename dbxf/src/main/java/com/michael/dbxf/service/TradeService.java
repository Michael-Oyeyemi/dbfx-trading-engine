package com.michael.dbxf.service;

import com.michael.dbxf.model.Order;
import com.michael.dbxf.model.Portfolio;
import com.michael.dbxf.model.Position;
import com.michael.dbxf.repository.OrderRepository;
import com.michael.dbxf.repository.PortfolioRepository;
import com.michael.dbxf.repository.PositionRepository;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Service
public class TradeService {

    private final PortfolioRepository portfolioRepository;
    private final OrderRepository orderRepository;
    private final PositionRepository positionRepository;

    public TradeService(PortfolioRepository portfolioRepository,
                        OrderRepository orderRepository,
                        PositionRepository positionRepository) {
        this.portfolioRepository = portfolioRepository;
        this.orderRepository = orderRepository;
        this.positionRepository = positionRepository;
    }

    @Retryable(
            retryFor = ObjectOptimisticLockingFailureException.class,
            maxAttempts = 3,
            backoff = @Backoff(delay = 100)
    )
    @Transactional
    public Order executeTrade(Long portfolioId, String ticker, String side, BigDecimal price, Integer quantity) {

        Portfolio portfolio = portfolioRepository.findById(portfolioId)
                .orElseThrow(() -> new IllegalArgumentException("Portfolio not found for ID: " + portfolioId));

        BigDecimal totalCost = price.multiply(BigDecimal.valueOf(quantity));
        String upperTicker = ticker.toUpperCase();

        Position position = positionRepository.findByPortfolioIdAndTicker(portfolioId, upperTicker)
                .orElseGet(() -> {
                    Position p = new Position();
                    p.setPortfolioId(portfolioId);
                    p.setTicker(upperTicker);
                    p.setQuantity(0);
                    return p;
                });

        if ("BUY".equalsIgnoreCase(side)) {
            if (portfolio.getBalance().compareTo(totalCost) < 0) {
                throw new IllegalStateException("Insufficient funds to execute BUY order.");
            }
            portfolio.setBalance(portfolio.getBalance().subtract(totalCost));
            position.setQuantity(position.getQuantity() + quantity);

        } else if ("SELL".equalsIgnoreCase(side)) {
            if (position.getQuantity() < quantity) {
                throw new IllegalStateException("Insufficient share holdings to execute SELL order.");
            }
            portfolio.setBalance(portfolio.getBalance().add(totalCost));
            position.setQuantity(position.getQuantity() - quantity);

        } else {
            throw new IllegalArgumentException("Invalid trade side: " + side);
        }

        portfolioRepository.save(portfolio);
        positionRepository.save(position);

        Order order = new Order();
        order.setTicker(upperTicker);
        order.setSide(side.toUpperCase());
        order.setPrice(price);
        order.setQuantity(quantity);
        order.setTimestamp(LocalDateTime.now());

        return orderRepository.save(order);
    }
}