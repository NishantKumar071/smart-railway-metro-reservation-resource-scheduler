-- =============================================================================
-- SmartRail AI+ — AI History / Synthetic Training Data
-- =============================================================================
-- DISCLAIMER: All data below is SYNTHETIC data generated algorithmically
-- for academic demonstration purposes. It does NOT represent real historical
-- Indian Railways booking or cancellation records.
-- Models trained on this data are for demonstration only.
-- =============================================================================

USE smartrail_db;

-- Waitlist prediction history records (synthetic)
-- Columns: train characteristics, days_before_journey, wl_number, was_confirmed
DROP TABLE IF EXISTS ai_waitlist_history;
CREATE TABLE ai_waitlist_history (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    train_number        VARCHAR(10),
    travel_class        VARCHAR(5),
    quota               VARCHAR(20),
    journey_month       INT,     -- 1-12
    days_before_journey INT,     -- days between booking and journey
    waitlist_number     INT,     -- WL position at time of booking
    total_wl_at_time    INT,     -- total waitlist at time of booking
    max_wl_allowed      INT,     -- maximum waitlist for this class
    historical_cancel_rate FLOAT, -- historical cancellation rate for this train/class
    is_holiday_period   TINYINT(1), -- is this a peak/holiday period
    was_confirmed       TINYINT(1)  -- target: 1=got confirmed, 0=remained WL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert ~300 synthetic training records
-- Pattern: lower WL + more days + non-peak = higher confirmation chance
INSERT INTO ai_waitlist_history
    (train_number, travel_class, quota, journey_month, days_before_journey, waitlist_number, total_wl_at_time, max_wl_allowed, historical_cancel_rate, is_holiday_period, was_confirmed)
VALUES
-- Confirmed cases (WL1-5, 15+ days before, non-peak)
('12301', 'SL',  'GENERAL', 2,  30, 1,  3,  50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 3,  25, 2,  5,  50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 7,  20, 1,  2,  50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 9,  28, 3,  7,  50, 0.35, 0, 1),
('12301', '3AC', 'GENERAL', 1,  22, 1,  4,  20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 4,  18, 2,  6,  20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 6,  30, 1,  2,  20, 0.28, 0, 1),
('12301', '2AC', 'GENERAL', 8,  25, 1,  3,  10, 0.22, 0, 1),
('12951', 'SL',  'GENERAL', 2,  28, 2,  4,  50, 0.30, 0, 1),
('12951', 'SL',  'GENERAL', 5,  20, 3,  8,  50, 0.30, 0, 1),
('12951', '3AC', 'GENERAL', 3,  22, 1,  3,  20, 0.25, 0, 1),
('12627', 'SL',  'GENERAL', 7,  18, 4,  9,  50, 0.32, 0, 1),
('12627', 'SL',  'GENERAL', 9,  25, 2,  5,  50, 0.32, 0, 1),
('12627', '3AC', 'GENERAL', 11, 30, 1,  2,  20, 0.26, 0, 1),
('12017', 'CC',  'GENERAL', 1,  15, 1,  2,  10, 0.20, 0, 1),
('12017', 'CC',  'GENERAL', 6,  20, 2,  4,  10, 0.20, 0, 1),
('22691', '3AC', 'GENERAL', 4,  25, 1,  3,  20, 0.22, 0, 1),
('22691', '2AC', 'GENERAL', 8,  18, 1,  2,  10, 0.18, 0, 1),
('12433', '3AC', 'GENERAL', 2,  22, 2,  5,  20, 0.27, 0, 1),
('12433', '3AC', 'TATKAL',  3,  7,  1,  2,  10, 0.15, 0, 1),
-- More confirmed with TATKAL (higher confirmation due to premium)
('12301', 'SL',  'TATKAL',  5,  5,  1,  2,  15, 0.35, 0, 1),
('12301', 'SL',  'TATKAL',  8,  3,  2,  3,  15, 0.35, 0, 1),
('12951', '3AC', 'TATKAL',  7,  4,  1,  1,  10, 0.30, 0, 1),
-- Senior Citizen quota - higher priority
('12301', 'SL',  'SENIOR_CITIZEN', 1, 20, 1, 2, 15, 0.35, 0, 1),
('12951', '3AC', 'SENIOR_CITIZEN', 6, 15, 1, 3, 10, 0.30, 0, 1),
-- Confirmed in peak but low WL
('12301', 'SL',  'GENERAL', 10, 30, 2,  4,  50, 0.35, 1, 1),
('12301', '3AC', 'GENERAL', 12, 28, 1,  2,  20, 0.28, 1, 1),
('12951', 'SL',  'GENERAL', 10, 25, 3,  6,  50, 0.30, 1, 1),
('12627', '3AC', 'GENERAL', 12, 30, 2,  4,  20, 0.26, 1, 1),
-- Borderline cases (WL 6-15, 10-20 days)
('12301', 'SL',  'GENERAL', 3,  15, 8,  15, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 6,  12, 10, 18, 50, 0.35, 0, 1),
('12951', '3AC', 'GENERAL', 4,  14, 7,  12, 20, 0.25, 0, 0),
('12627', 'SL',  'GENERAL', 8,  10, 12, 20, 50, 0.32, 0, 0),
('12433', '3AC', 'GENERAL', 5,  12, 9,  16, 20, 0.27, 0, 0),
-- Not confirmed (high WL, peak, few days)
('12301', 'SL',  'GENERAL', 10, 3,  35, 48, 50, 0.35, 1, 0),
('12301', 'SL',  'GENERAL', 12, 5,  40, 50, 50, 0.35, 1, 0),
('12951', 'SL',  'GENERAL', 10, 2,  45, 50, 50, 0.30, 1, 0),
('12951', '3AC', 'GENERAL', 12, 4,  18, 20, 20, 0.25, 1, 0),
('12627', 'SL',  'GENERAL', 10, 3,  48, 50, 50, 0.32, 1, 0),
('12627', '3AC', 'GENERAL', 12, 2,  19, 20, 20, 0.26, 1, 0),
('12433', '3AC', 'GENERAL', 11, 5,  16, 20, 20, 0.27, 1, 0),
('12433', 'SL',  'GENERAL', 10, 1,  50, 50, 50, 0.27, 1, 0),
-- Not confirmed: low days, high WL
('12301', 'SL',  'GENERAL', 7,  2,  25, 40, 50, 0.35, 0, 0),
('12951', 'SL',  'GENERAL', 9,  1,  30, 45, 50, 0.30, 0, 0),
('12627', '3AC', 'GENERAL', 5,  3,  18, 20, 20, 0.26, 0, 0),
-- More confirmed varied cases
('12301', 'SL',  'GENERAL', 1,  25, 5,  10, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 2,  22, 6,  12, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 4,  28, 4,  8,  50, 0.35, 0, 1),
('12951', '3AC', 'GENERAL', 7,  20, 5,  10, 20, 0.25, 0, 1),
('12951', '2AC', 'GENERAL', 3,  22, 3,  6,  10, 0.22, 0, 1),
-- More not-confirmed varied cases
('12301', 'SL',  'GENERAL', 10, 8,  30, 42, 50, 0.35, 1, 0),
('12301', '3AC', 'GENERAL', 12, 6,  16, 20, 20, 0.28, 1, 0),
('12951', 'SL',  'GENERAL', 10, 7,  38, 48, 50, 0.30, 1, 0),
('12627', 'SL',  'GENERAL', 11, 5,  42, 50, 50, 0.32, 1, 0),
('12433', '3AC', 'GENERAL', 10, 4,  17, 20, 20, 0.27, 1, 0),
-- Additional balanced samples
('12301', 'SL',  'GENERAL', 5,  18, 7,  14, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 8,  14, 9,  18, 50, 0.35, 0, 0),
('12951', 'SL',  'GENERAL', 6,  16, 11, 20, 50, 0.30, 0, 0),
('12627', '3AC', 'GENERAL', 2,  26, 4,  8,  20, 0.26, 0, 1),
('22691', '3AC', 'GENERAL', 7,  12, 8,  15, 20, 0.22, 0, 1),
('22691', '3AC', 'GENERAL', 9,  5,  12, 18, 20, 0.22, 0, 0),
('12017', 'CC',  'GENERAL', 10, 8,  5,  9,  10, 0.20, 1, 0),
('12017', 'CC',  'GENERAL', 4,  22, 2,  4,  10, 0.20, 0, 1),
('12433', '3AC', 'GENERAL', 8,  18, 6,  12, 20, 0.27, 0, 1),
('12433', 'SL',  'GENERAL', 9,  10, 20, 35, 50, 0.27, 0, 0),
-- Emergency quota - almost always confirmed
('12301', 'SL',  'EMERGENCY', 5, 10, 1, 2, 10, 0.35, 0, 1),
('12951', '3AC', 'EMERGENCY', 8, 7,  1, 1, 10, 0.30, 1, 1),
-- More diverse train/class combos
('12301', '1AC', 'GENERAL', 3,  20, 1, 2, 5, 0.15, 0, 1),
('12301', '1AC', 'GENERAL', 10, 5,  3, 5, 5, 0.15, 1, 0),
('12951', '1AC', 'GENERAL', 7,  25, 1, 2, 5, 0.15, 0, 1),
('12627', '1AC', 'GENERAL', 12, 3,  4, 5, 5, 0.12, 1, 0),
-- Various months and patterns
('12301', 'SL',  'GENERAL', 1, 20, 12, 22, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 2, 25, 8,  16, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 3, 18, 15, 28, 50, 0.35, 0, 0),
('12301', 'SL',  'GENERAL', 4, 22, 10, 20, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 5, 15, 18, 32, 50, 0.35, 0, 0),
('12301', 'SL',  'GENERAL', 6, 28, 5,  10, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 7, 12, 22, 38, 50, 0.35, 0, 0),
('12301', 'SL',  'GENERAL', 8, 25, 7,  14, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 9, 10, 25, 42, 50, 0.35, 0, 0),
('12301', 'SL',  'GENERAL', 10, 20, 20, 36, 50, 0.35, 1, 0),
('12301', 'SL',  'GENERAL', 11, 28, 6,  12, 50, 0.35, 0, 1),
('12301', 'SL',  'GENERAL', 12, 5,  38, 48, 50, 0.35, 1, 0),
-- Concurrency test supporting data
('12301', '3AC', 'GENERAL', 1, 15, 1, 2, 20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 2, 20, 2, 4, 20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 3, 25, 3, 6, 20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 4, 10, 8, 15, 20, 0.28, 0, 0),
('12301', '3AC', 'GENERAL', 5, 8,  12, 18, 20, 0.28, 0, 0),
('12301', '3AC', 'GENERAL', 6, 30, 1, 2, 20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 7, 15, 5, 10, 20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 8, 5,  15, 20, 20, 0.28, 1, 0),
('12301', '3AC', 'GENERAL', 9, 20, 4, 8, 20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 10, 3, 18, 20, 20, 0.28, 1, 0),
('12301', '3AC', 'GENERAL', 11, 25, 2, 5, 20, 0.28, 0, 1),
('12301', '3AC', 'GENERAL', 12, 7, 16, 20, 20, 0.28, 1, 0);

-- Recommendation history
DROP TABLE IF EXISTS ai_recommendation_history;
CREATE TABLE ai_recommendation_history (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source_station      VARCHAR(10),
    dest_station        VARCHAR(10),
    travel_class        VARCHAR(5),
    journey_month       INT,
    day_of_week         INT,  -- 0=Mon, 6=Sun
    budget_range        VARCHAR(20),  -- LOW/MEDIUM/HIGH
    preferred_time      VARCHAR(20),  -- MORNING/AFTERNOON/EVENING/NIGHT
    recommended_train   VARCHAR(10),
    was_booked          TINYINT(1),  -- Did user book the recommended train?
    user_rating         INT          -- NULL or 1-5 rating
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO ai_recommendation_history
    (source_station, dest_station, travel_class, journey_month, day_of_week, budget_range, preferred_time, recommended_train, was_booked, user_rating)
VALUES
('NDLS', 'HWH',  'SL',  1,  0, 'LOW',    'EVENING', '12301', 1, 5),
('NDLS', 'HWH',  '3AC', 3,  2, 'MEDIUM', 'EVENING', '12301', 1, 4),
('NDLS', 'BCT',  '3AC', 5,  4, 'MEDIUM', 'EVENING', '12951', 1, 4),
('NDLS', 'BCT',  '2AC', 8,  5, 'HIGH',   'EVENING', '12951', 1, 5),
('NDLS', 'SBC',  'SL',  10, 1, 'LOW',    'NIGHT',   '12627', 1, 3),
('NDLS', 'SBC',  '3AC', 12, 6, 'MEDIUM', 'NIGHT',   '12627', 0, NULL),
('NDLS', 'PNBE', '3AC', 2,  3, 'MEDIUM', 'EVENING', '12433', 1, 4),
('NDLS', 'BPL',  'CC',  7,  0, 'MEDIUM', 'MORNING', '12001', 1, 5),
('NDLS', 'DDN',  'CC',  9,  2, 'MEDIUM', 'MORNING', '12017', 1, 4),
('DDN',  'NDLS', '3AC', 11, 4, 'MEDIUM', 'MORNING', '22691', 1, 5),
('NDLS', 'HWH',  'SL',  10, 6, 'LOW',    'EVENING', '12301', 1, 3),
('NDLS', 'BCT',  'SL',  12, 5, 'LOW',    'NIGHT',   '12951', 0, NULL),
('NDLS', 'DDN',  'CC',  1,  1, 'LOW',    'MORNING', '12017', 1, 5),
('NDLS', 'DDN',  '2AC', 6,  3, 'HIGH',   'MORNING', '12017', 1, 4);

SELECT 'SmartRail AI+ AI history data loaded successfully.' AS status;
