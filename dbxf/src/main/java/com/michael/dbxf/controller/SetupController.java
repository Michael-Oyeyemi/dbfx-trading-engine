package com.michael.dbxf.controller;

import com.michael.dbxf.dto.SetupRequest;
import com.michael.dbxf.service.SetupService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/portfolio")
public class SetupController {

    private final SetupService setupService;

    public SetupController(SetupService setupService) {
        this.setupService = setupService;
    }

    @PostMapping("/setup")
    public ResponseEntity<String> setupEnvironment(@RequestBody SetupRequest request) {
        setupService.initializeEnvironment(request);
        return ResponseEntity.ok("DBXF Environment dynamically seeded successfully.");
    }
}