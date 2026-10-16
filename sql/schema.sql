-- ==============================================================================
-- SMART RAILWAY RESERVATION & RESOURCE SCHEDULER (OS + DBMS)
-- Team ID: OSDBMS-V-2026-T281
-- Team Leader: Nishant Kumar | Team Member: Robert Sandi Thomas
-- Target DBMS: MySQL Server 8.0.46 | Engine: InnoDB (ACID Compliant)
-- ==============================================================================

DROP DATABASE IF EXISTS smart_railway_db;
CREATE DATABASE smart_railway_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_railway_db;

-- ------------------------------------------------------------------------------
-- 1. STATIONS TABLE: Real Indian Railway station codes and zones
-- ------------------------------------------------------------------------------
CREATE TABLE stations (
    station_code VARCHAR(10) PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    zone VARCHAR(10) NOT NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 2. TRAINS TABLE: Real Indian Railways Trains (Vande Bharat, Rajdhani, etc.)
-- ------------------------------------------------------------------------------
CREATE TABLE trains (
    train_number VARCHAR(10) PRIMARY KEY,
    train_name VARCHAR(100) NOT NULL,
    train_type VARCHAR(50) NOT NULL,
    source_station VARCHAR(10) NOT NULL,
    dest_station VARCHAR(10) NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    total_coaches INT DEFAULT 16,
    distance_km INT NOT NULL,
    FOREIGN KEY (source_station) REFERENCES stations(station_code) ON UPDATE CASCADE,
    FOREIGN KEY (dest_station) REFERENCES stations(station_code) ON UPDATE CASCADE,
    INDEX idx_train_route (source_station, dest_station)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 3. TRAIN COACHES & CLASSES
-- ------------------------------------------------------------------------------
CREATE TABLE train_coaches (
    coach_id INT AUTO_INCREMENT PRIMARY KEY,
    train_number VARCHAR(10) NOT NULL,
    coach_name VARCHAR(10) NOT NULL,
    coach_class VARCHAR(10) NOT NULL, -- 'CC', 'EC', '3A', '2A', '1A', 'SL'
    capacity INT NOT NULL DEFAULT 72,
    base_fare DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (train_number) REFERENCES trains(train_number) ON DELETE CASCADE,
    INDEX idx_train_class (train_number, coach_class)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 4. SEAT INVENTORY: High-concurrency row-locked inventory per date & class
-- ------------------------------------------------------------------------------
CREATE TABLE seat_inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    train_number VARCHAR(10) NOT NULL,
    travel_date DATE NOT NULL,
    coach_class VARCHAR(10) NOT NULL,
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,
    total_wl_seats INT NOT NULL DEFAULT 50,
    current_wl_count INT NOT NULL DEFAULT 0,
    version INT NOT NULL DEFAULT 1,
    FOREIGN KEY (train_number) REFERENCES trains(train_number) ON DELETE CASCADE,
    UNIQUE KEY uq_train_date_class (train_number, travel_date, coach_class),
    INDEX idx_inv_search (train_number, travel_date)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 5. PHYSICAL SEATS TABLE: Specific Coach & Seat Berths for Confirmed Bookings
-- ------------------------------------------------------------------------------
CREATE TABLE physical_seats (
    seat_id INT AUTO_INCREMENT PRIMARY KEY,
    train_number VARCHAR(10) NOT NULL,
    travel_date DATE NOT NULL,
    coach_name VARCHAR(10) NOT NULL,
    coach_class VARCHAR(10) NOT NULL,
    seat_number INT NOT NULL,
    berth_type VARCHAR(20) NOT NULL, -- LOWER, UPPER, MIDDLE, SIDE LOWER, SIDE UPPER, WINDOW
    is_booked BOOLEAN NOT NULL DEFAULT FALSE,
    current_pnr VARCHAR(15) NULL,
    FOREIGN KEY (train_number) REFERENCES trains(train_number) ON DELETE CASCADE,
    UNIQUE KEY uq_physical_seat (train_number, travel_date, coach_name, seat_number),
    INDEX idx_seat_alloc (train_number, travel_date, coach_class, is_booked)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 6. PASSENGERS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE passengers (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    age INT NOT NULL CHECK (age >= 1 AND age <= 125),
    gender VARCHAR(10) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 7. BOOKINGS TABLE: Complete Lifecycle (CONFIRMED, WAITING, CANCELLED)
-- ------------------------------------------------------------------------------
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    pnr VARCHAR(15) NOT NULL UNIQUE,
    train_number VARCHAR(10) NOT NULL,
    passenger_id INT NOT NULL,
    travel_date DATE NOT NULL,
    coach_class VARCHAR(10) NOT NULL,
    coach_name VARCHAR(10) NULL,
    seat_number INT NULL,
    berth_type VARCHAR(20) NULL,
    booking_status ENUM('CONFIRMED', 'WAITING', 'CANCELLED') NOT NULL,
    wl_position INT NULL,
    quota ENUM('EMERGENCY', 'SENIOR_CITIZEN', 'TATKAL', 'NORMAL') NOT NULL,
    priority_level INT NOT NULL, -- 1: EMERGENCY, 2: SENIOR_CITIZEN, 3: TATKAL, 4: NORMAL
    fare_paid DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (train_number) REFERENCES trains(train_number) ON DELETE CASCADE,
    FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id) ON DELETE CASCADE,
    INDEX idx_pnr (pnr),
    INDEX idx_train_date_status (train_number, travel_date, booking_status),
    INDEX idx_wl_promotion (train_number, travel_date, coach_class, booking_status, priority_level, wl_position)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 8. DBMS TRANSACTIONS AUDIT & TELEMETRY LOG
-- ------------------------------------------------------------------------------
CREATE TABLE db_transactions_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    thread_id INT NOT NULL,
    operation VARCHAR(50) NOT NULL,
    pnr VARCHAR(15) NULL,
    details TEXT NOT NULL,
    status ENUM('COMMITTED', 'ROLLEDBACK') NOT NULL,
    execution_time_ms DOUBLE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_thread (thread_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 9. OS SCHEDULING METRICS LOG
-- ------------------------------------------------------------------------------
CREATE TABLE os_scheduling_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    active_worker_threads INT NOT NULL,
    queue_size INT NOT NULL,
    emergency_served INT NOT NULL DEFAULT 0,
    senior_served INT NOT NULL DEFAULT 0,
    tatkal_served INT NOT NULL DEFAULT 0,
    normal_served INT NOT NULL DEFAULT 0,
    contention_events INT NOT NULL DEFAULT 0,
    avg_wait_time_ms DOUBLE NOT NULL DEFAULT 0.0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
