-- ==============================================================================
-- REAL INDIAN RAILWAYS SEED DATA
-- Team ID: OSDBMS-V-2026-T281 | Smart Railway Reservation System
-- ==============================================================================

USE smart_railway_db;

-- ------------------------------------------------------------------------------
-- 1. REAL INDIAN RAILWAY STATIONS
-- ------------------------------------------------------------------------------
INSERT INTO stations (station_code, station_name, city, state, zone) VALUES
('NDLS', 'New Delhi Railway Station', 'New Delhi', 'Delhi', 'NR'),
('MMCT', 'Mumbai Central', 'Mumbai', 'Maharashtra', 'WR'),
('HWH', 'Howrah Junction', 'Kolkata', 'West Bengal', 'ER'),
('MAS', 'MGR Chennai Central', 'Chennai', 'Tamil Nadu', 'SR'),
('SBC', 'KSR Bengaluru City', 'Bengaluru', 'Karnataka', 'SWR'),
('CNB', 'Kanpur Central', 'Kanpur', 'Uttar Pradesh', 'NCR'),
('BSB', 'Varanasi Junction', 'Varanasi', 'Uttar Pradesh', 'NR'),
('LKO', 'Lucknow Charbagh', 'Lucknow', 'Uttar Pradesh', 'NR'),
('PNBE', 'Patna Junction', 'Patna', 'Bihar', 'ECR'),
('PUNE', 'Pune Junction', 'Pune', 'Maharashtra', 'CR'),
('ADI', 'Ahmedabad Junction', 'Ahmedabad', 'Gujarat', 'WR'),
('TVC', 'Thiruvananthapuram Central', 'Thiruvananthapuram', 'Kerala', 'SR');

-- ------------------------------------------------------------------------------
-- 2. REAL INDIAN RAILWAY TRAINS
-- ------------------------------------------------------------------------------
INSERT INTO trains (train_number, train_name, train_type, source_station, dest_station, departure_time, arrival_time, total_coaches, distance_km) VALUES
('22436', 'Vande Bharat Express', 'VANDE BHARAT', 'NDLS', 'BSB', '06:00:00', '14:00:00', 16, 759),
('22435', 'Vande Bharat Express', 'VANDE BHARAT', 'BSB', 'NDLS', '15:00:00', '23:00:00', 16, 759),
('12952', 'Mumbai Rajdhani Express', 'RAJDHANI', 'NDLS', 'MMCT', '16:55:00', '08:35:00', 20, 1386),
('12951', 'Mumbai Rajdhani Express', 'RAJDHANI', 'MMCT', 'NDLS', '17:00:00', '08:32:00', 20, 1386),
('12302', 'Howrah Rajdhani Express', 'RAJDHANI', 'NDLS', 'HWH', '16:50:00', '09:55:00', 18, 1451),
('12004', 'Lucknow Shatabdi Express', 'SHATABDI', 'NDLS', 'LKO', '06:10:00', '12:40:00', 14, 513),
('20608', 'Vande Bharat Express', 'VANDE BHARAT', 'SBC', 'MAS', '05:45:00', '10:10:00', 16, 359),
('12626', 'Kerala Express', 'SUPERFAST', 'NDLS', 'TVC', '20:10:00', '18:00:00', 22, 3036),
('12124', 'Deccan Queen', 'SUPERFAST', 'PUNE', 'MMCT', '07:15:00', '10:25:00', 14, 192),
('12932', 'Ahmedabad Double Decker', 'DOUBLE DECKER', 'ADI', 'MMCT', '06:00:00', '13:05:00', 12, 491);

-- ------------------------------------------------------------------------------
-- 3. COACH CONFIGURATIONS & CLASSES
-- ------------------------------------------------------------------------------
-- 22436 Vande Bharat (CC & EC)
INSERT INTO train_coaches (train_number, coach_name, coach_class, capacity, base_fare) VALUES
('22436', 'C1', 'CC', 78, 1750.00),
('22436', 'C2', 'CC', 78, 1750.00),
('22436', 'E1', 'EC', 52, 3300.00),

-- 12952 Mumbai Rajdhani (3A, 2A, 1A)
('12952', 'B1', '3A', 72, 2100.00),
('12952', 'B2', '3A', 72, 2100.00),
('12952', 'A1', '2A', 48, 3050.00),
('12952', 'H1', '1A', 24, 4950.00),

-- 12302 Howrah Rajdhani (3A, 2A)
('12302', 'B1', '3A', 72, 2250.00),
('12302', 'A1', '2A', 48, 3200.00),

-- 12004 Lucknow Shatabdi (CC, EC)
('12004', 'C1', 'CC', 78, 1165.00),
('12004', 'E1', 'EC', 52, 2125.00),

-- 20608 SBC-MAS Vande Bharat (CC, EC)
('20608', 'C1', 'CC', 78, 995.00),
('20608', 'E1', 'EC', 52, 1885.00),

-- 12626 Kerala Express (SL, 3A)
('12626', 'S1', 'SL', 72, 940.00),
('12626', 'B1', '3A', 72, 2480.00);

-- ------------------------------------------------------------------------------
-- 4. PROCEDURAL SEEDING OF DATES & SEAT INVENTORIES
-- Generates inventory and physical seats for the next 14 travel dates
-- ------------------------------------------------------------------------------
DELIMITER $$
DROP PROCEDURE IF EXISTS SeedTrainInventories$$
CREATE PROCEDURE SeedTrainInventories()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE curr_date DATE;
    DECLARE v_train VARCHAR(10);
    DECLARE v_class VARCHAR(10);
    DECLARE v_coach VARCHAR(10);
    DECLARE v_cap INT;
    DECLARE s INT;
    DECLARE b_type VARCHAR(20);
    
    -- Populate inventory for next 14 days
    WHILE i < 14 DO
        SET curr_date = DATE_ADD(CURDATE(), INTERVAL i DAY);
        
        -- Insert aggregated seat inventory per train & class
        INSERT INTO seat_inventory (train_number, travel_date, coach_class, total_seats, available_seats, total_wl_seats, current_wl_count)
        SELECT 
            train_number, 
            curr_date, 
            coach_class, 
            SUM(capacity) AS total_seats,
            -- For testing concurrency, reserve seats or leave 5 seats open on day 1 for immediate live testing
            IF(i = 0, 5, SUM(capacity)) AS available_seats,
            30 AS total_wl_seats,
            0 AS current_wl_count
        FROM train_coaches
        GROUP BY train_number, coach_class
        ON DUPLICATE KEY UPDATE available_seats = VALUES(available_seats);

        -- Insert physical seats for each coach (Generating standard 24 seats per coach for fast crisp testing)
        INSERT INTO physical_seats (train_number, travel_date, coach_name, coach_class, seat_number, berth_type, is_booked)
        SELECT 
            tc.train_number,
            curr_date,
            tc.coach_name,
            tc.coach_class,
            num.n,
            CASE (num.n % 6)
                WHEN 1 THEN 'LOWER'
                WHEN 2 THEN 'MIDDLE'
                WHEN 3 THEN 'UPPER'
                WHEN 4 THEN 'SIDE LOWER'
                WHEN 5 THEN 'SIDE UPPER'
                ELSE 'WINDOW'
            END,
            FALSE
        FROM train_coaches tc
        CROSS JOIN (
            SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 
            UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
            UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14 UNION SELECT 15
            UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
            UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24
        ) num
        WHERE num.n <= IF(i = 0, 5, 24)
        ON DUPLICATE KEY UPDATE is_booked = FALSE;

        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;

CALL SeedTrainInventories();
DROP PROCEDURE IF EXISTS SeedTrainInventories;

-- ------------------------------------------------------------------------------
-- 5. INITIAL SEED PASSENGERS & SAMPLE BOOKINGS FOR DEMO
-- ------------------------------------------------------------------------------
INSERT INTO passengers (full_name, age, gender, phone, email) VALUES
('Nishant Kumar', 22, 'Male', '9876543210', 'nishant.kumar@example.com'),
('Robert Sandi Thomas', 22, 'Male', '9876543211', 'robert.thomas@example.com'),
('Dr. Ramesh Sharma', 65, 'Male', '9876543212', 'ramesh.sharma@example.com'),
('Col. Vikramaditya Rathore', 45, 'Male', '9876543213', 'vikram.defence@gov.in'),
('Priya Sundaram', 28, 'Female', '9876543214', 'priya.s@example.com');
