package com.michael.dbxf.repository;

import com.michael.dbxf.model.Position;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface PositionRepository extends JpaRepository<Position, Long> {
    Optional<Position> findByPortfolioIdAndTicker(Long portfolioId, String ticker);
    List<Position> findByPortfolioId(Long portfolioId);
}