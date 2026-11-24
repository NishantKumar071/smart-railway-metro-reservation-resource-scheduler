-- =============================================================================
-- SmartRail AI+ — Database Schema
-- University: Graphic Era (Deemed to be University), Dehradun
-- Team: OSDBMS-V-2026-T281
-- =============================================================================
-- IMPORTANT: This database contains DEMONSTRATION data only.
-- This system is NOT connected to live IRCTC or Indian Railways systems.
-- All train numbers, PNRs, and passenger details are fictional.
-- =============================================================================

-- Create and select database
CREATE DATABASE IF NOT EXISTS smartrail_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smartrail_db;

-- =============================================================================
-- TABLE 1: users
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    username        VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    phone           VARCHAR(15),
    date_of_birth   DATE,
    gender          ENUM('MALE','FEMALE','OTHER') DEFAULT 'OTHER',
    role            ENUM('PASSENGER','ADMIN') DEFAULT 'PASSENGER',
    is_active       TINYINT(1) DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login      DATETIME,
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 2: stations
-- =============================================================================
CREATE TABLE IF NOT EXISTS stations (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    station_code    VARCHAR(10) NOT NULL UNIQUE,
    station_name    VARCHAR(200) NOT NULL,
    city            VARCHAR(100) NOT NULL,
    state           VARCHAR(100) NOT NULL,
    zone            VARCHAR(50),
    latitude        DECIMAL(10,7),
    longitude       DECIMAL(10,7),
    is_major        TINYINT(1) DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code (station_code),
    INDEX idx_city (city)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 3: trains
-- =============================================================================
CREATE TABLE IF NOT EXISTS trains (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    train_number    VARCHAR(10) NOT NULL UNIQUE,
    train_name      VARCHAR(200) NOT NULL,
    train_type      ENUM('SUPERFAST','EXPRESS','PASSENGER','RAJDHANI','SHATABDI','DURONTO','VANDE_BHARAT','LOCAL') DEFAULT 'EXPRESS',
    source_station  VARCHAR(10) NOT NULL,
    dest_station    VARCHAR(10) NOT NULL,
    departure_time  TIME NOT NULL,
    arrival_time    TIME NOT NULL,
    journey_duration_mins INT UNSIGNED NOT NULL,
    runs_on         VARCHAR(20) DEFAULT '1234567',  -- Days: 1=Mon...7=Sun
    is_active       TINYINT(1) DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_train_number (train_number),
    INDEX idx_source (source_station),
    INDEX idx_dest (dest_station),
    FOREIGN KEY (source_station) REFERENCES stations(station_code) ON UPDATE CASCADE,
    FOREIGN KEY (dest_station) REFERENCES stations(station_code) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 4: train_routes (intermediate stops)
-- =============================================================================
CREATE TABLE IF NOT EXISTS train_routes (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    train_id        INT UNSIGNED NOT NULL,
    station_code    VARCHAR(10) NOT NULL,
    stop_number     INT UNSIGNED NOT NULL,
    arrival_time    TIME,
    departure_time  TIME,
    halt_minutes    INT DEFAULT 0,
    distance_km     FLOAT DEFAULT 0,
    day_offset      INT DEFAULT 0,  -- 0=same day, 1=next day
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_train_stop (train_id, stop_number),
    UNIQUE KEY uk_train_station (train_id, station_code),
    INDEX idx_station (station_code),
    FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE,
    FOREIGN KEY (station_code) REFERENCES stations(station_code) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 5: train_coaches
-- =============================================================================
CREATE TABLE IF NOT EXISTS train_coaches (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    train_id        INT UNSIGNED NOT NULL,
    coach_number    VARCHAR(10) NOT NULL,
    coach_type      ENUM('1AC','2AC','3AC','SL','CC','2S','FC','EC') NOT NULL,
    total_seats     INT UNSIGNED NOT NULL,
    berth_config    JSON,  -- {"lower":X,"middle":Y,"upper":Z,"side_lower":W,"side_upper":V}
    fare_per_km     DECIMAL(6,2) DEFAULT 0.50,
    base_fare       DECIMAL(8,2) DEFAULT 50.00,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_train_coach (train_id, coach_number),
    INDEX idx_coach_type (coach_type),
    FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 6: seat_inventory
-- =============================================================================
CREATE TABLE IF NOT EXISTS seat_inventory (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    train_id            INT UNSIGNED NOT NULL,
    coach_id            INT UNSIGNED NOT NULL,
    journey_date        DATE NOT NULL,
    total_seats         INT UNSIGNED NOT NULL,
    confirmed_count     INT UNSIGNED DEFAULT 0,
    rac_count           INT UNSIGNED DEFAULT 0,
    waitlist_count      INT UNSIGNED DEFAULT 0,
    max_waitlist        INT UNSIGNED DEFAULT 20,
    available_seats     INT UNSIGNED NOT NULL,
    fare_sl             DECIMAL(8,2),
    fare_3ac            DECIMAL(8,2),
    fare_2ac            DECIMAL(8,2),
    fare_1ac            DECIMAL(8,2),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_inventory (train_id, coach_id, journey_date),
    INDEX idx_journey_date (journey_date),
    FOREIGN KEY (train_id) REFERENCES trains(id),
    FOREIGN KEY (coach_id) REFERENCES train_coaches(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 7: physical_seats
-- =============================================================================
CREATE TABLE IF NOT EXISTS physical_seats (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    coach_id        INT UNSIGNED NOT NULL,
    seat_number     VARCHAR(10) NOT NULL,
    berth_type      ENUM('LOWER','MIDDLE','UPPER','SIDE_LOWER','SIDE_UPPER','WINDOW','AISLE') NOT NULL,
    is_window       TINYINT(1) DEFAULT 0,
    bay_number      INT UNSIGNED,  -- compartment/bay number
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_seat (coach_id, seat_number),
    INDEX idx_coach (coach_id),
    FOREIGN KEY (coach_id) REFERENCES train_coaches(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 8: passengers (master list of passenger profiles)
-- =============================================================================
CREATE TABLE IF NOT EXISTS passengers (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED,
    full_name       VARCHAR(200) NOT NULL,
    age             INT UNSIGNED NOT NULL,
    gender          ENUM('MALE','FEMALE','OTHER') NOT NULL,
    id_type         ENUM('AADHAAR','PAN','PASSPORT','DL','VOTER_ID') DEFAULT 'AADHAAR',
    id_number       VARCHAR(50),
    phone           VARCHAR(15),
    is_senior       TINYINT(1) DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 9: bookings
-- =============================================================================
CREATE TABLE IF NOT EXISTS bookings (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pnr                 VARCHAR(10) NOT NULL UNIQUE,
    user_id             INT UNSIGNED NOT NULL,
    train_id            INT UNSIGNED NOT NULL,
    coach_id            INT UNSIGNED NOT NULL,
    journey_date        DATE NOT NULL,
    source_station      VARCHAR(10) NOT NULL,
    dest_station        VARCHAR(10) NOT NULL,
    travel_class        ENUM('1AC','2AC','3AC','SL','CC','2S') NOT NULL,
    quota               ENUM('GENERAL','TATKAL','SENIOR_CITIZEN','EMERGENCY','LADIES') DEFAULT 'GENERAL',
    priority_level      INT DEFAULT 3,  -- 1=Emergency,2=Senior,3=Tatkal,4=Normal
    booking_status      ENUM('CONFIRMED','WAITING','RAC','CANCELLED') DEFAULT 'CONFIRMED',
    total_fare          DECIMAL(10,2) NOT NULL,
    payment_status      ENUM('PAID','PENDING','REFUNDED') DEFAULT 'PAID',
    booking_time        DATETIME DEFAULT CURRENT_TIMESTAMP,
    cancellation_time   DATETIME,
    cancellation_reason VARCHAR(500),
    request_id          VARCHAR(36),  -- UUID for OS scheduling
    processing_thread   INT,          -- Worker thread ID (OS concept)
    processing_time_ms  INT,          -- Time taken to process (OS telemetry)
    ai_recommendation   TINYINT(1) DEFAULT 0,  -- Was this AI-recommended?
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_pnr (pnr),
    INDEX idx_user (user_id),
    INDEX idx_train_date (train_id, journey_date),
    INDEX idx_status (booking_status),
    INDEX idx_booking_time (booking_time),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (train_id) REFERENCES trains(id),
    FOREIGN KEY (coach_id) REFERENCES train_coaches(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 10: booking_passengers
-- =============================================================================
CREATE TABLE IF NOT EXISTS booking_passengers (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    booking_id      INT UNSIGNED NOT NULL,
    passenger_id    INT UNSIGNED NOT NULL,
    seat_id         INT UNSIGNED,  -- NULL if waitlisted
    berth_type      ENUM('LOWER','MIDDLE','UPPER','SIDE_LOWER','SIDE_UPPER','NO_PREFERENCE'),
    berth_allotted  ENUM('LOWER','MIDDLE','UPPER','SIDE_LOWER','SIDE_UPPER'),
    coach_number    VARCHAR(10),
    seat_number     VARCHAR(10),
    waitlist_number INT,  -- NULL if confirmed
    passenger_fare  DECIMAL(8,2),
    status          ENUM('CONFIRMED','WAITING','RAC','CANCELLED') DEFAULT 'CONFIRMED',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_booking (booking_id),
    INDEX idx_passenger (passenger_id),
    INDEX idx_seat (seat_id),
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (passenger_id) REFERENCES passengers(id),
    FOREIGN KEY (seat_id) REFERENCES physical_seats(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 11: booking_status_history
-- =============================================================================
CREATE TABLE IF NOT EXISTS booking_status_history (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    booking_id      INT UNSIGNED NOT NULL,
    old_status      VARCHAR(20),
    new_status      VARCHAR(20) NOT NULL,
    reason          VARCHAR(500),
    changed_by      INT UNSIGNED,  -- user_id
    changed_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_booking (booking_id),
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 12: db_transactions_log
-- =============================================================================
CREATE TABLE IF NOT EXISTS db_transactions_log (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    transaction_id  VARCHAR(36) NOT NULL,  -- UUID
    operation_type  ENUM('BOOKING','CANCELLATION','WAITLIST_UPGRADE','ADMIN') NOT NULL,
    table_affected  VARCHAR(100),
    rows_affected   INT DEFAULT 0,
    status          ENUM('STARTED','COMMITTED','ROLLED_BACK','FAILED') NOT NULL,
    error_message   TEXT,
    duration_ms     INT,
    initiated_by    INT UNSIGNED,  -- user_id
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_txn_id (transaction_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 13: os_scheduling_metrics
-- =============================================================================
CREATE TABLE IF NOT EXISTS os_scheduling_metrics (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    request_id              VARCHAR(36) NOT NULL,
    request_type            VARCHAR(50),
    priority_level          INT DEFAULT 4,
    priority_name           VARCHAR(20) DEFAULT 'NORMAL',
    queue_wait_time_ms      INT DEFAULT 0,
    processing_time_ms      INT DEFAULT 0,
    total_time_ms           INT DEFAULT 0,
    worker_thread_id        INT,
    queue_position_at_entry INT,
    result_status           ENUM('COMPLETED','FAILED','CANCELLED') DEFAULT 'COMPLETED',
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_request (request_id),
    INDEX idx_priority (priority_level),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- TABLE 14: ai_prediction_logs
-- =============================================================================
CREATE TABLE IF NOT EXISTS ai_prediction_logs (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    prediction_type     ENUM('WAITLIST','RECOMMENDATION','SEAT') NOT NULL,
    input_data          JSON NOT NULL,
    output_data         JSON NOT NULL,
    model_version       VARCHAR(50),
    prediction_score    FLOAT,
    confidence_level    ENUM('HIGH','MEDIUM','LOW') DEFAULT 'MEDIUM',
    was_accurate        TINYINT(1),  -- NULL until outcome known
    user_id             INT UNSIGNED,
    booking_id          INT UNSIGNED,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (prediction_type),
    INDEX idx_user (user_id),
    INDEX idx_booking (booking_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================================
-- STORED PROCEDURES
-- =============================================================================

DELIMITER $$

-- Generate a unique PNR
CREATE PROCEDURE IF NOT EXISTS generate_pnr(OUT new_pnr VARCHAR(10))
BEGIN
    DECLARE pnr_candidate VARCHAR(10);
    DECLARE pnr_exists INT;
    SET pnr_candidate = CONCAT(
        LPAD(FLOOR(RAND() * 9000000000 + 1000000000), 10, '0')
    );
    SELECT COUNT(*) INTO pnr_exists FROM bookings WHERE pnr = pnr_candidate;
    WHILE pnr_exists > 0 DO
        SET pnr_candidate = CONCAT(
            LPAD(FLOOR(RAND() * 9000000000 + 1000000000), 10, '0')
        );
        SELECT COUNT(*) INTO pnr_exists FROM bookings WHERE pnr = pnr_candidate;
    END WHILE;
    SET new_pnr = pnr_candidate;
END$$

-- Get current waitlist count for a train/class/date
CREATE PROCEDURE IF NOT EXISTS get_waitlist_count(
    IN p_train_id INT UNSIGNED,
    IN p_coach_id INT UNSIGNED,
    IN p_journey_date DATE,
    OUT p_count INT
)
BEGIN
    SELECT COUNT(*) INTO p_count
    FROM bookings b
    JOIN booking_passengers bp ON b.id = bp.booking_id
    WHERE b.train_id = p_train_id
      AND b.coach_id = p_coach_id
      AND b.journey_date = p_journey_date
      AND bp.status = 'WAITING';
END$$

DELIMITER ;

-- =============================================================================
-- VIEWS
-- =============================================================================

CREATE OR REPLACE VIEW v_booking_summary AS
SELECT
    b.pnr,
    b.booking_status,
    b.journey_date,
    b.travel_class,
    b.total_fare,
    b.booking_time,
    u.full_name AS booked_by,
    u.email,
    t.train_number,
    t.train_name,
    s_src.station_name AS source,
    s_dst.station_name AS destination,
    t.departure_time,
    t.arrival_time,
    COUNT(bp.id) AS passenger_count
FROM bookings b
JOIN users u ON b.user_id = u.id
JOIN trains t ON b.train_id = t.id
JOIN stations s_src ON b.source_station = s_src.station_code
JOIN stations s_dst ON b.dest_station = s_dst.station_code
JOIN booking_passengers bp ON b.id = bp.booking_id
GROUP BY b.id;

CREATE OR REPLACE VIEW v_seat_availability AS
SELECT
    t.train_number,
    t.train_name,
    si.journey_date,
    tc.coach_type,
    si.total_seats,
    si.available_seats,
    si.confirmed_count,
    si.waitlist_count,
    si.max_waitlist
FROM seat_inventory si
JOIN trains t ON si.train_id = t.id
JOIN train_coaches tc ON si.coach_id = tc.id;

CREATE OR REPLACE VIEW v_os_telemetry AS
SELECT
    COUNT(*) AS total_requests,
    SUM(CASE WHEN result_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_requests,
    SUM(CASE WHEN result_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_requests,
    AVG(processing_time_ms) AS avg_processing_time_ms,
    AVG(queue_wait_time_ms) AS avg_queue_wait_ms,
    MAX(queue_position_at_entry) AS max_queue_depth,
    AVG(total_time_ms) AS avg_total_time_ms
FROM os_scheduling_metrics
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR);
