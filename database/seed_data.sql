-- =============================================================================
-- SmartRail AI+ — Seed Data (DEMONSTRATION DATA ONLY)
-- =============================================================================
-- DISCLAIMER: All data below is fictional and created for academic demonstration
-- purposes only. Train numbers, station codes, fares, and schedules do NOT
-- represent actual Indian Railways timetables or services.
-- =============================================================================

USE smartrail_db;

-- =============================================================================
-- STATIONS (20 major Indian railway stations - demonstration data)
-- =============================================================================
INSERT IGNORE INTO stations (station_code, station_name, city, state, zone, latitude, longitude, is_major) VALUES
('NDLS', 'New Delhi Railway Station',       'New Delhi',    'Delhi',             'NR',  28.6428, 77.2197, 1),
('BCT',  'Mumbai Central',                   'Mumbai',       'Maharashtra',       'WR',  18.9690, 72.8205, 1),
('MAS',  'Chennai Central',                  'Chennai',      'Tamil Nadu',        'SR',  13.0827, 80.2707, 1),
('HWH',  'Howrah Junction',                  'Howrah',       'West Bengal',       'ER',  22.5839, 88.3421, 1),
('SBC',  'KSR Bengaluru City Junction',      'Bangalore',    'Karnataka',         'SWR', 12.9771, 77.5713, 1),
('SC',   'Secunderabad Junction',            'Hyderabad',    'Telangana',         'SCR', 17.4399, 78.4983, 1),
('JP',   'Jaipur Junction',                  'Jaipur',       'Rajasthan',         'NWR', 26.9124, 75.7873, 1),
('ADI',  'Ahmedabad Junction',               'Ahmedabad',    'Gujarat',           'WR',  23.0225, 72.5714, 1),
('LKO',  'Lucknow Charbagh',                 'Lucknow',      'Uttar Pradesh',     'NR',  26.8467, 80.9462, 1),
('PNBE', 'Patna Junction',                   'Patna',        'Bihar',             'ECR', 25.5941, 85.1376, 1),
('BPL',  'Bhopal Junction',                  'Bhopal',       'Madhya Pradesh',    'WCR', 23.2599, 77.4126, 1),
('NAG',  'Nagpur Junction',                  'Nagpur',       'Maharashtra',       'CR',  21.1458, 79.0882, 1),
('CNB',  'Kanpur Central',                   'Kanpur',       'Uttar Pradesh',     'NCR', 26.4499, 80.3319, 1),
('AGC',  'Agra Cantt',                       'Agra',         'Uttar Pradesh',     'NCR', 27.1767, 78.0081, 1),
('DDN',  'Dehradun',                         'Dehradun',     'Uttarakhand',       'NR',  30.3165, 78.0322, 1),
('HRW',  'Haridwar Junction',                'Haridwar',     'Uttarakhand',       'NR',  29.9457, 78.1642, 0),
('RKSH', 'Rishikesh',                         'Rishikesh',    'Uttarakhand',       'NR',  30.0869, 78.2676, 0),
('MFP',  'Muzaffarpur Junction',             'Muzaffarpur',  'Bihar',             'ECR', 26.1197, 85.3910, 0),
('PUNE', 'Pune Junction',                    'Pune',         'Maharashtra',       'CR',  18.5204, 73.8567, 1),
('JAT',  'Jammu Tawi',                       'Jammu',        'J&K',               'NR',  32.7266, 74.8570, 1);

-- =============================================================================
-- TRAINS (10 demonstration trains)
-- =============================================================================
INSERT IGNORE INTO trains (train_number, train_name, train_type, source_station, dest_station, departure_time, arrival_time, journey_duration_mins, runs_on) VALUES
('12001', 'Bhopal Shatabdi Express',          'SHATABDI',    'NDLS', 'BPL',  '06:00:00', '13:55:00', 475,  '1234567'),
('12301', 'Howrah Rajdhani Express',          'RAJDHANI',    'NDLS', 'HWH',  '16:55:00', '10:00:00', 1025, '1234567'),
('12951', 'Mumbai Rajdhani Express',          'RAJDHANI',    'NDLS', 'BCT',  '17:00:00', '08:35:00', 935,  '1234567'),
('12627', 'Karnataka Express',                'SUPERFAST',   'NDLS', 'SBC',  '20:30:00', '05:30:00', 1740, '1234567'),
('12433', 'Rajdhani Express (Raxaul)',        'RAJDHANI',    'NDLS', 'PNBE', '20:15:00', '05:30:00', 555,  '1234567'),
('22691', 'Rajdhani Express (DDN-NDLS)',      'RAJDHANI',    'DDN',  'NDLS', '05:17:00', '08:35:00', 198,  '1234567'),
('12017', 'Dehradun Shatabdi',               'SHATABDI',    'NDLS', 'DDN',  '06:45:00', '11:50:00', 305,  '1234567'),
('12036', 'Prayagraj Express',               'SUPERFAST',   'NDLS', 'PNBE', '19:10:00', '07:40:00', 750,  '1234567'),
('12925', 'Paschim Express',                 'SUPERFAST',   'BCT',  'NDLS', '23:00:00', '21:40:00', 1360, '1234567'),
('12137', 'Punjab Mail',                     'EXPRESS',     'BCT',  'JAT',  '19:30:00', '07:35:00', 725,  '1234567');

-- =============================================================================
-- TRAIN ROUTES
-- =============================================================================
-- Train 22691: Dehradun to New Delhi
INSERT IGNORE INTO train_routes (train_id, station_code, stop_number, arrival_time, departure_time, halt_minutes, distance_km, day_offset)
SELECT t.id, 'DDN',  1, NULL,       '05:17:00', 0,   0,   0 FROM trains t WHERE t.train_number = '22691'
UNION ALL
SELECT t.id, 'HRW',  2, '05:50:00', '05:52:00', 2,   54,  0 FROM trains t WHERE t.train_number = '22691'
UNION ALL
SELECT t.id, 'RKSH', 3, '06:12:00', '06:14:00', 2,   74,  0 FROM trains t WHERE t.train_number = '22691'
UNION ALL
SELECT t.id, 'LKO',  4, '07:40:00', '07:45:00', 5,   220, 0 FROM trains t WHERE t.train_number = '22691'
UNION ALL
SELECT t.id, 'CNB',  5, '08:10:00', '08:12:00', 2,   280, 0 FROM trains t WHERE t.train_number = '22691'
UNION ALL
SELECT t.id, 'NDLS', 6, '08:35:00', NULL,       0,   305, 0 FROM trains t WHERE t.train_number = '22691';

-- Train 12017: New Delhi to Dehradun
INSERT IGNORE INTO train_routes (train_id, station_code, stop_number, arrival_time, departure_time, halt_minutes, distance_km, day_offset)
SELECT t.id, 'NDLS', 1, NULL,       '06:45:00', 0,   0,   0 FROM trains t WHERE t.train_number = '12017'
UNION ALL
SELECT t.id, 'CNB',  2, '08:10:00', '08:15:00', 5,   65,  0 FROM trains t WHERE t.train_number = '12017'
UNION ALL
SELECT t.id, 'LKO',  3, '08:40:00', '08:43:00', 3,   120, 0 FROM trains t WHERE t.train_number = '12017'
UNION ALL
SELECT t.id, 'HRW',  4, '10:40:00', '10:42:00', 2,   260, 0 FROM trains t WHERE t.train_number = '12017'
UNION ALL
SELECT t.id, 'RKSH', 5, '11:00:00', '11:02:00', 2,   280, 0 FROM trains t WHERE t.train_number = '12017'
UNION ALL
SELECT t.id, 'DDN',  6, '11:50:00', NULL,       0,   305, 0 FROM trains t WHERE t.train_number = '12017';

-- Train 12001: NDLS to BPL
INSERT IGNORE INTO train_routes (train_id, station_code, stop_number, arrival_time, departure_time, halt_minutes, distance_km, day_offset)
SELECT t.id, 'NDLS', 1, NULL,       '06:00:00', 0,   0,   0 FROM trains t WHERE t.train_number = '12001'
UNION ALL
SELECT t.id, 'AGC',  2, '07:35:00', '07:37:00', 2,   195, 0 FROM trains t WHERE t.train_number = '12001'
UNION ALL
SELECT t.id, 'BPL',  3, '13:55:00', NULL,       0,   692, 0 FROM trains t WHERE t.train_number = '12001';

-- =============================================================================
-- TRAIN COACHES
-- =============================================================================
-- For each train, add SL, 3AC, 2AC, 1AC coaches

-- Train 12017 (Dehradun Shatabdi) - CC coaches
INSERT IGNORE INTO train_coaches (train_id, coach_number, coach_type, total_seats, fare_per_km, base_fare)
SELECT t.id, 'C1', 'CC', 78, 2.10, 300.00 FROM trains t WHERE t.train_number = '12017'
UNION ALL
SELECT t.id, 'C2', 'CC', 78, 2.10, 300.00 FROM trains t WHERE t.train_number = '12017'
UNION ALL
SELECT t.id, 'EC', 'EC', 56, 3.50, 500.00 FROM trains t WHERE t.train_number = '12017';

-- Train 22691 (DDN Rajdhani)
INSERT IGNORE INTO train_coaches (train_id, coach_number, coach_type, total_seats, fare_per_km, base_fare)
SELECT t.id, 'B1', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '22691'
UNION ALL
SELECT t.id, 'B2', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '22691'
UNION ALL
SELECT t.id, 'A1', '2AC', 46, 2.80, 350.00 FROM trains t WHERE t.train_number = '22691'
UNION ALL
SELECT t.id, 'H1', '1AC', 24, 4.50, 600.00 FROM trains t WHERE t.train_number = '22691';

-- Train 12301 (Howrah Rajdhani)
INSERT IGNORE INTO train_coaches (train_id, coach_number, coach_type, total_seats, fare_per_km, base_fare)
SELECT t.id, 'S1', 'SL',  72, 0.80, 100.00 FROM trains t WHERE t.train_number = '12301'
UNION ALL
SELECT t.id, 'S2', 'SL',  72, 0.80, 100.00 FROM trains t WHERE t.train_number = '12301'
UNION ALL
SELECT t.id, 'B1', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '12301'
UNION ALL
SELECT t.id, 'B2', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '12301'
UNION ALL
SELECT t.id, 'A1', '2AC', 46, 2.80, 350.00 FROM trains t WHERE t.train_number = '12301'
UNION ALL
SELECT t.id, 'H1', '1AC', 24, 4.50, 600.00 FROM trains t WHERE t.train_number = '12301';

-- Train 12951 (Mumbai Rajdhani)
INSERT IGNORE INTO train_coaches (train_id, coach_number, coach_type, total_seats, fare_per_km, base_fare)
SELECT t.id, 'S1', 'SL',  72, 0.80, 100.00 FROM trains t WHERE t.train_number = '12951'
UNION ALL
SELECT t.id, 'B1', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '12951'
UNION ALL
SELECT t.id, 'B2', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '12951'
UNION ALL
SELECT t.id, 'A1', '2AC', 46, 2.80, 350.00 FROM trains t WHERE t.train_number = '12951'
UNION ALL
SELECT t.id, 'H1', '1AC', 24, 4.50, 600.00 FROM trains t WHERE t.train_number = '12951';

-- Train 12627 (Karnataka Express)
INSERT IGNORE INTO train_coaches (train_id, coach_number, coach_type, total_seats, fare_per_km, base_fare)
SELECT t.id, 'S1', 'SL',  72, 0.80, 100.00 FROM trains t WHERE t.train_number = '12627'
UNION ALL
SELECT t.id, 'S2', 'SL',  72, 0.80, 100.00 FROM trains t WHERE t.train_number = '12627'
UNION ALL
SELECT t.id, 'S3', 'SL',  72, 0.80, 100.00 FROM trains t WHERE t.train_number = '12627'
UNION ALL
SELECT t.id, 'B1', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '12627'
UNION ALL
SELECT t.id, 'B2', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '12627'
UNION ALL
SELECT t.id, 'A1', '2AC', 46, 2.80, 350.00 FROM trains t WHERE t.train_number = '12627';

-- Train 12433 (Rajdhani NDLS-PNBE)
INSERT IGNORE INTO train_coaches (train_id, coach_number, coach_type, total_seats, fare_per_km, base_fare)
SELECT t.id, 'B1', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '12433'
UNION ALL
SELECT t.id, 'B2', '3AC', 72, 1.90, 200.00 FROM trains t WHERE t.train_number = '12433'
UNION ALL
SELECT t.id, 'A1', '2AC', 46, 2.80, 350.00 FROM trains t WHERE t.train_number = '12433'
UNION ALL
SELECT t.id, 'H1', '1AC', 24, 4.50, 600.00 FROM trains t WHERE t.train_number = '12433';

-- =============================================================================
-- PHYSICAL SEATS — Generate seats for the first coach of train 12301 B1 (3AC 72 seats)
-- This provides enough seats for the concurrency test (2 available out of 72)
-- =============================================================================
INSERT IGNORE INTO physical_seats (coach_id, seat_number, berth_type, is_window, bay_number)
SELECT
    tc.id,
    CONCAT(n.seat_num),
    CASE
        WHEN (n.seat_num % 8) IN (1, 4) THEN 'LOWER'
        WHEN (n.seat_num % 8) IN (2, 5) THEN 'MIDDLE'
        WHEN (n.seat_num % 8) IN (3, 6) THEN 'UPPER'
        WHEN (n.seat_num % 8) IN (7) THEN 'SIDE_LOWER'
        ELSE 'SIDE_UPPER'
    END,
    CASE WHEN (n.seat_num % 8) IN (1,2,3,7) THEN 1 ELSE 0 END,
    CEIL(n.seat_num / 8)
FROM train_coaches tc
JOIN (
    SELECT a.N + b.N * 10 + 1 AS seat_num
    FROM
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7) a,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7) b
    WHERE a.N + b.N * 10 + 1 <= 72
) n
WHERE tc.coach_number = 'B1'
  AND tc.train_id = (SELECT id FROM trains WHERE train_number = '12301');

-- =============================================================================
-- USERS (demonstration accounts - passwords are bcrypt hashes of shown values)
-- Admin: admin@smartrail.local / Admin@123
-- User:  nishant@smartrail.local / User@123
-- =============================================================================
-- bcrypt hashes (cost=12) generated offline — these are demonstration hashes only.
-- Do NOT use these passwords for real systems.

INSERT IGNORE INTO users (email, username, password_hash, full_name, phone, gender, role) VALUES
('admin@smartrail.local',    'admin',         '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'System Administrator', '9999999999', 'MALE',   'ADMIN'),
('nishant@smartrail.local',  'nishant',       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'Nishant Kumar',       '9876543210', 'MALE',   'PASSENGER'),
('robert@smartrail.local',   'robert',        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'Robert Sandi Thomas', '9876543211', 'MALE',   'PASSENGER'),
('demo_user@smartrail.local','demo_user',     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'Demo Passenger',      '9000000001', 'FEMALE', 'PASSENGER'),
('test_user@smartrail.local','test_user',     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUdfufCB7PLt3GS8UQ/fiFi.S', 'Test User',           '9000000002', 'OTHER',  'PASSENGER');

-- NOTE: All above passwords hash to "Demo@123" for initial login.
-- You MUST change these in production. Admin panel forces password change on first login.

-- =============================================================================
-- SEAT INVENTORY — Populate for next 60 days for each coach/train combo
-- =============================================================================
INSERT IGNORE INTO seat_inventory (train_id, coach_id, journey_date, total_seats, available_seats, confirmed_count, waitlist_count, max_waitlist)
SELECT
    tc.train_id,
    tc.id,
    DATE_ADD(CURDATE(), INTERVAL seq.n DAY),
    tc.total_seats,
    tc.total_seats,  -- Initially all available
    0,
    0,
    CASE WHEN tc.coach_type = 'SL' THEN 50 WHEN tc.coach_type IN ('3AC','2AC') THEN 20 ELSE 10 END
FROM train_coaches tc
JOIN (
    SELECT 0 AS n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
    UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9
    UNION SELECT 10 UNION SELECT 11 UNION SELECT 12 UNION SELECT 13 UNION SELECT 14
    UNION SELECT 15 UNION SELECT 16 UNION SELECT 17 UNION SELECT 18 UNION SELECT 19
    UNION SELECT 20 UNION SELECT 21 UNION SELECT 22 UNION SELECT 23 UNION SELECT 24
    UNION SELECT 25 UNION SELECT 26 UNION SELECT 27 UNION SELECT 28 UNION SELECT 29
    UNION SELECT 30 UNION SELECT 31 UNION SELECT 32 UNION SELECT 33 UNION SELECT 34
    UNION SELECT 35 UNION SELECT 36 UNION SELECT 37 UNION SELECT 38 UNION SELECT 39
    UNION SELECT 40 UNION SELECT 41 UNION SELECT 42 UNION SELECT 43 UNION SELECT 44
    UNION SELECT 45 UNION SELECT 46 UNION SELECT 47 UNION SELECT 48 UNION SELECT 49
    UNION SELECT 50 UNION SELECT 51 UNION SELECT 52 UNION SELECT 53 UNION SELECT 54
    UNION SELECT 55 UNION SELECT 56 UNION SELECT 57 UNION SELECT 58 UNION SELECT 59
) seq;

-- =============================================================================
-- SAMPLE BOOKINGS (demonstration)
-- =============================================================================
INSERT IGNORE INTO bookings (pnr, user_id, train_id, coach_id, journey_date, source_station, dest_station, travel_class, quota, priority_level, booking_status, total_fare, payment_status)
SELECT
    '5101234567',
    u.id,
    t.id,
    tc.id,
    DATE_ADD(CURDATE(), INTERVAL 7 DAY),
    'NDLS', 'HWH', '3AC', 'GENERAL', 4, 'CONFIRMED', 1245.00, 'PAID'
FROM users u, trains t, train_coaches tc
WHERE u.username = 'nishant'
  AND t.train_number = '12301'
  AND tc.train_id = t.id AND tc.coach_number = 'B1'
LIMIT 1;

INSERT IGNORE INTO bookings (pnr, user_id, train_id, coach_id, journey_date, source_station, dest_station, travel_class, quota, priority_level, booking_status, total_fare, payment_status)
SELECT
    '5109876543',
    u.id,
    t.id,
    tc.id,
    DATE_ADD(CURDATE(), INTERVAL 14 DAY),
    'NDLS', 'DDN', 'CC', 'GENERAL', 4, 'CONFIRMED', 540.00, 'PAID'
FROM users u, trains t, train_coaches tc
WHERE u.username = 'robert'
  AND t.train_number = '12017'
  AND tc.train_id = t.id AND tc.coach_number = 'C1'
LIMIT 1;

-- Sample passengers
INSERT IGNORE INTO passengers (user_id, full_name, age, gender, id_type)
SELECT u.id, 'Nishant Kumar', 21, 'MALE', 'AADHAAR' FROM users u WHERE u.username = 'nishant';

INSERT IGNORE INTO passengers (user_id, full_name, age, gender, id_type)
SELECT u.id, 'Robert Sandi Thomas', 22, 'MALE', 'AADHAAR' FROM users u WHERE u.username = 'robert';

-- Link passengers to bookings
INSERT IGNORE INTO booking_passengers (booking_id, passenger_id, berth_type, berth_allotted, coach_number, seat_number, passenger_fare, status)
SELECT b.id, p.id, 'LOWER', 'LOWER', 'B1', '1', 1245.00, 'CONFIRMED'
FROM bookings b
JOIN passengers p ON p.full_name = 'Nishant Kumar'
WHERE b.pnr = '5101234567'
LIMIT 1;

INSERT IGNORE INTO booking_passengers (booking_id, passenger_id, berth_type, berth_allotted, coach_number, seat_number, passenger_fare, status)
SELECT b.id, p.id, 'WINDOW', NULL, 'C1', '5', 540.00, 'CONFIRMED'
FROM bookings b
JOIN passengers p ON p.full_name = 'Robert Sandi Thomas'
WHERE b.pnr = '5109876543'
LIMIT 1;

-- Status history
INSERT IGNORE INTO booking_status_history (booking_id, old_status, new_status, reason)
SELECT id, NULL, 'CONFIRMED', 'Initial booking' FROM bookings WHERE pnr = '5101234567';

INSERT IGNORE INTO booking_status_history (booking_id, old_status, new_status, reason)
SELECT id, NULL, 'CONFIRMED', 'Initial booking' FROM bookings WHERE pnr = '5109876543';

-- Update seat inventory for the booked seats
UPDATE seat_inventory si
JOIN trains t ON si.train_id = t.id
JOIN train_coaches tc ON si.coach_id = tc.id
SET si.confirmed_count = si.confirmed_count + 1,
    si.available_seats = si.available_seats - 1
WHERE t.train_number = '12301'
  AND tc.coach_number = 'B1'
  AND si.journey_date = DATE_ADD(CURDATE(), INTERVAL 7 DAY);

UPDATE seat_inventory si
JOIN trains t ON si.train_id = t.id
JOIN train_coaches tc ON si.coach_id = tc.id
SET si.confirmed_count = si.confirmed_count + 1,
    si.available_seats = si.available_seats - 1
WHERE t.train_number = '12017'
  AND tc.coach_number = 'C1'
  AND si.journey_date = DATE_ADD(CURDATE(), INTERVAL 14 DAY);

-- Some OS telemetry sample data
INSERT IGNORE INTO os_scheduling_metrics (request_id, request_type, priority_level, priority_name, queue_wait_time_ms, processing_time_ms, total_time_ms, worker_thread_id, queue_position_at_entry, result_status)
VALUES
(UUID(), 'BOOKING', 4, 'NORMAL',    5,   124, 129, 1, 1, 'COMPLETED'),
(UUID(), 'BOOKING', 3, 'TATKAL',    2,   98,  100, 2, 2, 'COMPLETED'),
(UUID(), 'BOOKING', 2, 'SENIOR',    1,   87,  88,  3, 1, 'COMPLETED'),
(UUID(), 'BOOKING', 1, 'EMERGENCY', 0,   76,  76,  1, 1, 'COMPLETED'),
(UUID(), 'CANCEL',  4, 'NORMAL',    8,   145, 153, 4, 3, 'COMPLETED'),
(UUID(), 'BOOKING', 4, 'NORMAL',    12,  167, 179, 5, 5, 'COMPLETED'),
(UUID(), 'BOOKING', 3, 'TATKAL',    3,   102, 105, 2, 2, 'COMPLETED'),
(UUID(), 'BOOKING', 4, 'NORMAL',    15,  189, 204, 6, 6, 'FAILED');

SELECT 'SmartRail AI+ seed data loaded successfully.' AS status;
