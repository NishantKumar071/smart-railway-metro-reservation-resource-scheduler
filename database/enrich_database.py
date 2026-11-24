"""
SmartRail AI+ — Complete Database Enrichment Script
Populates:
  - 54 Major Indian Railway Stations across all zones
  - 30 Comprehensive Train Routes (both directions with realistic intermediate stops)
  - All coach classes: 1AC, 2AC, 3AC, SL, CC, EC, 2S
  - Generates 90 days of seat inventory for all trains and coaches
  - Generates realistic physical berths
"""

import sqlite3
import datetime
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "backend", "smartrail_embedded.db")

print(f"[Enrichment] Connecting to database: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. 54 STATIONS
stations = [
    ('NDLS', 'New Delhi Railway Station', 'New Delhi', 'Delhi', 'NR', 28.6428, 77.2197, 1),
    ('DLI', 'Old Delhi Junction', 'Delhi', 'Delhi', 'NR', 28.6609, 77.2307, 1),
    ('NZM', 'Hazrat Nizamuddin', 'New Delhi', 'Delhi', 'NR', 28.5888, 77.2536, 1),
    ('ANVT', 'Anand Vihar Terminal', 'Delhi', 'Delhi', 'NR', 28.6508, 77.3153, 1),
    ('BCT', 'Mumbai Central', 'Mumbai', 'Maharashtra', 'WR', 18.9690, 72.8205, 1),
    ('CSMT', 'Chhatrapati Shivaji Maharaj Terminus', 'Mumbai', 'Maharashtra', 'CR', 18.9400, 72.8354, 1),
    ('BDTS', 'Bandra Terminus', 'Mumbai', 'Maharashtra', 'WR', 19.0607, 72.8407, 1),
    ('HWH', 'Howrah Junction', 'Howrah', 'West Bengal', 'ER', 22.5839, 88.3421, 1),
    ('SDAH', 'Sealdah', 'Kolkata', 'West Bengal', 'ER', 22.5675, 88.3712, 1),
    ('MAS', 'Chennai Central', 'Chennai', 'Tamil Nadu', 'SR', 13.0827, 80.2707, 1),
    ('MS', 'Chennai Egmore', 'Chennai', 'Tamil Nadu', 'SR', 13.0782, 80.2605, 1),
    ('SBC', 'KSR Bengaluru City Junction', 'Bangalore', 'Karnataka', 'SWR', 12.9771, 77.5713, 1),
    ('YPR', 'Yesvantpur Junction', 'Bangalore', 'Karnataka', 'SWR', 13.0238, 77.5503, 1),
    ('SC', 'Secunderabad Junction', 'Hyderabad', 'Telangana', 'SCR', 17.4399, 78.4983, 1),
    ('HYB', 'Hyderabad Deccan', 'Hyderabad', 'Telangana', 'SCR', 17.3926, 78.4682, 1),
    ('BPL', 'Bhopal Junction', 'Bhopal', 'Madhya Pradesh', 'WCR', 23.2599, 77.4126, 1),
    ('RKMP', 'Rani Kamlapati', 'Bhopal', 'Madhya Pradesh', 'WCR', 23.2081, 77.4332, 1),
    ('AGC', 'Agra Cantt', 'Agra', 'Uttar Pradesh', 'NCR', 27.1767, 78.0081, 1),
    ('GWL', 'Gwalior Junction', 'Gwalior', 'Madhya Pradesh', 'NCR', 26.2166, 78.1884, 1),
    ('JHS', 'VGL Jhansi Junction', 'Jhansi', 'Uttar Pradesh', 'NCR', 25.4484, 78.5685, 1),
    ('CNB', 'Kanpur Central', 'Kanpur', 'Uttar Pradesh', 'NCR', 26.4499, 80.3319, 1),
    ('LKO', 'Lucknow Charbagh', 'Lucknow', 'Uttar Pradesh', 'NR', 26.8467, 80.9462, 1),
    ('PRYJ', 'Prayagraj Junction', 'Prayagraj', 'Uttar Pradesh', 'NCR', 25.4358, 81.8463, 1),
    ('BSB', 'Varanasi Junction', 'Varanasi', 'Uttar Pradesh', 'NR', 25.3176, 82.9739, 1),
    ('DDU', 'Pt. Deen Dayal Upadhyaya Junction', 'Mughalsarai', 'Uttar Pradesh', 'ECR', 25.2818, 83.1197, 1),
    ('PNBE', 'Patna Junction', 'Patna', 'Bihar', 'ECR', 25.5941, 85.1376, 1),
    ('GAYA', 'Gaya Junction', 'Gaya', 'Bihar', 'ECR', 24.7914, 85.0002, 1),
    ('DHN', 'Dhanbad Junction', 'Dhanbad', 'Jharkhand', 'ECR', 23.7957, 86.4304, 1),
    ('RNC', 'Ranchi Junction', 'Ranchi', 'Jharkhand', 'SER', 23.3441, 85.3096, 1),
    ('DDN', 'Dehradun Terminal', 'Dehradun', 'Uttarakhand', 'NR', 30.3165, 78.0322, 1),
    ('HRW', 'Haridwar Junction', 'Haridwar', 'Uttarakhand', 'NR', 29.9457, 78.1642, 1),
    ('RKSH', 'Rishikesh', 'Rishikesh', 'Uttarakhand', 'NR', 30.0869, 78.2676, 0),
    ('JP', 'Jaipur Junction', 'Jaipur', 'Rajasthan', 'NWR', 26.9124, 75.7873, 1),
    ('KOTA', 'Kota Junction', 'Kota', 'Rajasthan', 'WCR', 25.1800, 75.8300, 1),
    ('ADI', 'Ahmedabad Junction', 'Ahmedabad', 'Gujarat', 'WR', 23.0225, 72.5714, 1),
    ('BRC', 'Vadodara Junction', 'Vadodara', 'Gujarat', 'WR', 22.3072, 73.1812, 1),
    ('ST', 'Surat', 'Surat', 'Gujarat', 'WR', 21.1702, 72.8311, 1),
    ('PUNE', 'Pune Junction', 'Pune', 'Maharashtra', 'CR', 18.5204, 73.8567, 1),
    ('NAG', 'Nagpur Junction', 'Nagpur', 'Maharashtra', 'CR', 21.1458, 79.0882, 1),
    ('CDG', 'Chandigarh Junction', 'Chandigarh', 'Chandigarh', 'NR', 30.7046, 76.8277, 1),
    ('ASR', 'Amritsar Junction', 'Amritsar', 'Punjab', 'NR', 31.6340, 74.8723, 1),
    ('JAT', 'Jammu Tawi', 'Jammu', 'J&K', 'NR', 32.7266, 74.8570, 1),
    ('SVDK', 'SMVD Katra', 'Katra', 'J&K', 'NR', 32.9922, 74.9318, 1),
    ('GKP', 'Gorakhpur Junction', 'Gorakhpur', 'Uttar Pradesh', 'NER', 26.7606, 83.3732, 1),
    ('GHY', 'Guwahati', 'Guwahati', 'Assam', 'NFR', 26.1820, 91.7513, 1),
    ('BBS', 'Bhubaneswar', 'Bhubaneswar', 'Odisha', 'ECoR', 20.2961, 85.8245, 1),
    ('PURI', 'Puri', 'Puri', 'Odisha', 'ECoR', 19.8135, 85.8312, 1),
    ('VSKP', 'Visakhapatnam', 'Visakhapatnam', 'Andhra Pradesh', 'ECoR', 17.6868, 83.2185, 1),
    ('BZA', 'Vijayawada Junction', 'Vijayawada', 'Andhra Pradesh', 'SCR', 16.5062, 80.6480, 1),
    ('TVC', 'Thiruvananthapuram Central', 'Trivandrum', 'Kerala', 'SR', 8.5241, 76.9366, 1),
    ('ERS', 'Ernakulam Junction', 'Kochi', 'Kerala', 'SR', 9.9816, 76.2999, 1),
    ('MAO', 'Madgaon Junction', 'Goa', 'Goa', 'KR', 15.2832, 73.9667, 1),
    ('INDB', 'Indore Junction', 'Indore', 'Madhya Pradesh', 'WR', 22.7196, 75.8577, 1),
    ('UJN', 'Ujjain Junction', 'Ujjain', 'Madhya Pradesh', 'WR', 23.1765, 75.7885, 1)
]

cur.executemany("""
INSERT OR REPLACE INTO stations (station_code, station_name, city, state, zone, latitude, longitude, is_major)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", stations)
print(f"✓ Seeded {len(stations)} Major Stations.")

# 2. 30 COMPREHENSIVE TRAINS
trains = [
    (1, '12001', 'Bhopal Shatabdi Express', 'SHATABDI', 'NDLS', 'BPL', '06:00:00', '13:55:00', 475),
    (2, '12002', 'New Delhi Shatabdi Express', 'SHATABDI', 'BPL', 'NDLS', '15:00:00', '22:50:00', 470),
    (3, '12301', 'Howrah Rajdhani Express', 'RAJDHANI', 'NDLS', 'HWH', '16:55:00', '10:00:00', 1025),
    (4, '12302', 'New Delhi Rajdhani Express', 'RAJDHANI', 'HWH', 'NDLS', '16:50:00', '10:05:00', 1035),
    (5, '12951', 'Mumbai Rajdhani Express', 'RAJDHANI', 'NDLS', 'BCT', '17:00:00', '08:35:00', 935),
    (6, '12952', 'New Delhi Rajdhani Express', 'RAJDHANI', 'BCT', 'NDLS', '17:00:00', '08:35:00', 935),
    (7, '12627', 'Karnataka Express', 'SUPERFAST', 'NDLS', 'SBC', '20:30:00', '05:30:00', 1740),
    (8, '12628', 'Karnataka Express', 'SUPERFAST', 'SBC', 'NDLS', '19:20:00', '09:00:00', 1780),
    (9, '12017', 'Dehradun Shatabdi Express', 'SHATABDI', 'NDLS', 'DDN', '06:45:00', '11:50:00', 305),
    (10, '12018', 'New Delhi Shatabdi Express', 'SHATABDI', 'DDN', 'NDLS', '17:00:00', '22:15:00', 315),
    (11, '22691', 'Dehradun Rajdhani Express', 'RAJDHANI', 'DDN', 'NDLS', '05:17:00', '08:35:00', 198),
    (12, '22692', 'Dehradun Rajdhani Express', 'RAJDHANI', 'NDLS', 'DDN', '17:50:00', '21:10:00', 200),
    (13, '12433', 'Patna Rajdhani Express', 'RAJDHANI', 'NDLS', 'PNBE', '20:15:00', '05:30:00', 555),
    (14, '12434', 'Patna Rajdhani Express', 'RAJDHANI', 'PNBE', 'NDLS', '19:10:00', '07:40:00', 750),
    (15, '12615', 'Grand Trunk Express', 'SUPERFAST', 'NDLS', 'MAS', '18:40:00', '06:30:00', 2150),
    (16, '12616', 'Grand Trunk Express', 'SUPERFAST', 'MAS', 'NDLS', '19:15:00', '06:20:00', 2105),
    (17, '12723', 'Telangana Express', 'SUPERFAST', 'NDLS', 'HYB', '06:25:00', '08:00:00', 1535),
    (18, '12724', 'Telangana Express', 'SUPERFAST', 'HYB', 'NDLS', '06:25:00', '07:40:00', 1515),
    (19, '12137', 'Punjab Mail Express', 'EXPRESS', 'CSMT', 'NDLS', '19:35:00', '19:00:00', 1405),
    (20, '12138', 'Punjab Mail Express', 'EXPRESS', 'NDLS', 'CSMT', '05:15:00', '07:35:00', 1580),
    (21, '22436', 'Varanasi Vande Bharat', 'VANDE_BHARAT', 'NDLS', 'BSB', '06:00:00', '14:00:00', 480),
    (22, '22435', 'New Delhi Vande Bharat', 'VANDE_BHARAT', 'BSB', 'NDLS', '15:00:00', '23:00:00', 480),
    (23, '22439', 'Katra Vande Bharat', 'VANDE_BHARAT', 'NDLS', 'SVDK', '06:00:00', '14:00:00', 480),
    (24, '22440', 'New Delhi Vande Bharat', 'VANDE_BHARAT', 'SVDK', 'NDLS', '15:00:00', '23:00:00', 480),
    (25, '20901', 'Vande Bharat Express', 'VANDE_BHARAT', 'BCT', 'ADI', '06:10:00', '11:25:00', 315),
    (26, '20902', 'Vande Bharat Express', 'VANDE_BHARAT', 'ADI', 'BCT', '15:00:00', '20:25:00', 325),
    (27, '12059', 'Kota Jan Shatabdi', 'SUPERFAST', 'KOTA', 'NDLS', '05:55:00', '12:30:00', 395),
    (28, '12060', 'Kota Jan Shatabdi', 'SUPERFAST', 'NDLS', 'KOTA', '12:45:00', '19:30:00', 405),
    (29, '12414', 'Pooja Superfast Express', 'SUPERFAST', 'JAT', 'JP', '18:15:00', '09:45:00', 930),
    (30, '12413', 'Pooja Superfast Express', 'SUPERFAST', 'JP', 'JAT', '14:10:00', '07:30:00', 1040)
]

cur.executemany("""
INSERT OR REPLACE INTO trains (id, train_number, train_name, train_type, source_station, dest_station, departure_time, arrival_time, journey_duration_mins)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", trains)
print(f"✓ Seeded {len(trains)} Trains.")

# 3. INTERMEDIATE ROUTES & STOPS (Both directions for all 30 trains)
routes = [
    # 1. 12001: NDLS -> AGC -> GWL -> JHS -> BPL
    (1, 'NDLS', 1, None, '06:00:00', 0, 0),
    (1, 'AGC',  2, '07:35:00', '07:37:00', 2, 195),
    (1, 'GWL',  3, '08:40:00', '08:42:00', 2, 313),
    (1, 'JHS',  4, '09:40:00', '09:45:00', 5, 410),
    (1, 'BPL',  5, '13:55:00', None, 0, 700),

    # 2. 12002: BPL -> JHS -> GWL -> AGC -> NDLS
    (2, 'BPL',  1, None, '15:00:00', 0, 0),
    (2, 'JHS',  2, '18:45:00', '18:50:00', 5, 290),
    (2, 'GWL',  3, '19:48:00', '19:50:00', 2, 387),
    (2, 'AGC',  4, '21:05:00', '21:07:00', 2, 505),
    (2, 'NDLS', 5, '22:50:00', None, 0, 700),

    # 3. 12301: NDLS -> CNB -> PRYJ -> DDU -> GAYA -> DHN -> HWH
    (3, 'NDLS', 1, None, '16:55:00', 0, 0),
    (3, 'CNB',  2, '21:30:00', '21:35:00', 5, 440),
    (3, 'PRYJ', 3, '23:45:00', '23:47:00', 2, 635),
    (3, 'DDU',  4, '01:50:00', '02:00:00', 10, 785),
    (3, 'GAYA', 5, '04:00:00', '04:03:00', 3, 990),
    (3, 'DHN',  6, '06:40:00', '06:45:00', 5, 1190),
    (3, 'HWH',  7, '10:00:00', None, 0, 1450),

    # 4. 12302: HWH -> DHN -> GAYA -> DDU -> PRYJ -> CNB -> NDLS
    (4, 'HWH',  1, None, '16:50:00', 0, 0),
    (4, 'DHN',  2, '19:55:00', '20:00:00', 5, 260),
    (4, 'GAYA', 3, '22:30:00', '22:33:00', 3, 460),
    (4, 'DDU',  4, '00:45:00', '00:55:00', 10, 665),
    (4, 'PRYJ', 5, '02:50:00', '02:52:00', 2, 815),
    (4, 'CNB',  6, '05:25:00', '05:30:00', 5, 1010),
    (4, 'NDLS', 7, '10:05:00', None, 0, 1450),

    # 5. 12951: NDLS -> KOTA -> BRC -> ST -> BCT
    (5, 'NDLS', 1, None, '17:00:00', 0, 0),
    (5, 'KOTA', 2, '21:20:00', '21:25:00', 5, 465),
    (5, 'BRC',  3, '03:40:00', '03:48:00', 8, 990),
    (5, 'ST',   4, '05:10:00', '05:15:00', 5, 1120),
    (5, 'BCT',  5, '08:35:00', None, 0, 1385),

    # 6. 12952: BCT -> ST -> BRC -> KOTA -> NDLS
    (6, 'BCT',  1, None, '17:00:00', 0, 0),
    (6, 'ST',   2, '19:43:00', '19:48:00', 5, 265),
    (6, 'BRC',  3, '21:10:00', '21:18:00', 8, 395),
    (6, 'KOTA', 4, '03:40:00', '03:45:00', 5, 920),
    (6, 'NDLS', 5, '08:35:00', None, 0, 1385),

    # 7. 12627: Karnataka Express (NDLS -> AGC -> GWL -> JHS -> BPL -> NAG -> BZA -> SBC)
    (7, 'NDLS', 1, None, '20:30:00', 0, 0),
    (7, 'AGC',  2, '22:45:00', '22:50:00', 5, 195),
    (7, 'GWL',  3, '23:58:00', '00:03:00', 5, 313),
    (7, 'BPL',  4, '05:45:00', '05:55:00', 10, 700),
    (7, 'NAG',  5, '11:55:00', '12:05:00', 10, 1090),
    (7, 'BZA',  6, '21:15:00', '21:30:00', 15, 1665),
    (7, 'SBC',  7, '05:30:00', None, 0, 2400),

    # 8. 12628: Karnataka Express (SBC -> BZA -> NAG -> BPL -> JHS -> GWL -> AGC -> NDLS)
    (8, 'SBC',  1, None, '19:20:00', 0, 0),
    (8, 'BZA',  2, '03:45:00', '04:00:00', 15, 735),
    (8, 'NAG',  3, '13:00:00', '13:10:00', 10, 1310),
    (8, 'BPL',  4, '19:00:00', '19:10:00', 10, 1700),
    (8, 'JHS',  5, '23:30:00', '23:35:00', 5, 1990),
    (8, 'GWL',  6, '00:45:00', '00:50:00', 5, 2087),
    (8, 'AGC',  7, '02:05:00', '02:10:00', 5, 2205),
    (8, 'NDLS', 8, '09:00:00', None, 0, 2400),

    # 9. 12017: NDLS -> HRW -> DDN
    (9, 'NDLS', 1, None, '06:45:00', 0, 0),
    (9, 'HRW',  2, '10:40:00', '10:42:00', 2, 260),
    (9, 'DDN',  3, '11:50:00', None, 0, 305),

    # 10. 12018: DDN -> HRW -> NDLS
    (10, 'DDN',  1, None, '17:00:00', 0, 0),
    (10, 'HRW',  2, '18:10:00', '18:15:00', 5, 54),
    (10, 'NDLS', 3, '22:15:00', None, 0, 305),

    # 11. 22691: DDN -> HRW -> NDLS
    (11, 'DDN',  1, None, '05:17:00', 0, 0),
    (11, 'HRW',  2, '05:50:00', '05:52:00', 2, 54),
    (11, 'NDLS', 3, '08:35:00', None, 0, 305),

    # 12. 22692: NDLS -> HRW -> DDN
    (12, 'NDLS', 1, None, '17:50:00', 0, 0),
    (12, 'HRW',  2, '20:10:00', '20:12:00', 2, 260),
    (12, 'DDN',  3, '21:10:00', None, 0, 305),

    # 13. 12433: NDLS -> CNB -> DDU -> PNBE
    (13, 'NDLS', 1, None, '20:15:00', 0, 0),
    (13, 'CNB',  2, '00:50:00', '00:55:00', 5, 440),
    (13, 'DDU',  3, '04:55:00', '05:05:00', 10, 785),
    (13, 'PNBE', 4, '05:30:00', None, 0, 1000),

    # 14. 12434: PNBE -> DDU -> CNB -> NDLS
    (14, 'PNBE', 1, None, '19:10:00', 0, 0),
    (14, 'DDU',  2, '22:10:00', '22:20:00', 10, 215),
    (14, 'CNB',  3, '02:00:00', '02:05:00', 5, 560),
    (14, 'NDLS', 4, '07:40:00', None, 0, 1000),

    # 15. 12615: Grand Trunk (NDLS -> AGC -> BPL -> NAG -> BZA -> MAS)
    (15, 'NDLS', 1, None, '18:40:00', 0, 0),
    (15, 'AGC',  2, '21:10:00', '21:15:00', 5, 195),
    (15, 'BPL',  3, '04:15:00', '04:25:00', 10, 700),
    (15, 'NAG',  4, '10:40:00', '10:50:00', 10, 1090),
    (15, 'BZA',  5, '19:30:00', '19:40:00', 10, 1750),
    (15, 'MAS',  6, '06:30:00', None, 0, 2180),

    # 16. 12616: Grand Trunk (MAS -> BZA -> NAG -> BPL -> AGC -> NDLS)
    (16, 'MAS',  1, None, '19:15:00', 0, 0),
    (16, 'BZA',  2, '02:00:00', '02:10:00', 10, 430),
    (16, 'NAG',  3, '11:00:00', '11:10:00', 10, 1090),
    (16, 'BPL',  4, '17:25:00', '17:35:00', 10, 1480),
    (16, 'AGC',  5, '00:15:00', '00:20:00', 5, 1985),
    (16, 'NDLS', 6, '06:20:00', None, 0, 2180),

    # 17. 12723: Telangana Express (NDLS -> AGC -> BPL -> NAG -> SC -> HYB)
    (17, 'NDLS', 1, None, '06:25:00', 0, 0),
    (17, 'AGC',  2, '09:00:00', '09:05:00', 5, 195),
    (17, 'BPL',  3, '16:00:00', '16:10:00', 10, 700),
    (17, 'NAG',  4, '22:30:00', '22:40:00', 10, 1090),
    (17, 'SC',   5, '07:00:00', '07:15:00', 15, 1660),
    (17, 'HYB',  6, '08:00:00', None, 0, 1670),

    # 18. 12724: Telangana Express (HYB -> SC -> NAG -> BPL -> AGC -> NDLS)
    (18, 'HYB',  1, None, '06:25:00', 0, 0),
    (18, 'SC',   2, '06:45:00', '06:50:00', 5, 10),
    (18, 'NAG',  3, '15:20:00', '15:30:00', 10, 580),
    (18, 'BPL',  4, '21:40:00', '21:50:00', 10, 970),
    (18, 'AGC',  5, '04:30:00', '04:35:00', 5, 1475),
    (18, 'NDLS', 6, '07:40:00', None, 0, 1670),

    # 19. 12137: Punjab Mail Express (CSMT -> BPL -> JHS -> GWL -> AGC -> NDLS)
    (19, 'CSMT', 1, None, '19:35:00', 0, 0),
    (19, 'BPL',  2, '09:20:00', '09:30:00', 10, 835),
    (19, 'JHS',  3, '14:15:00', '14:25:00', 10, 1125),
    (19, 'GWL',  4, '15:35:00', '15:40:00', 5, 1222),
    (19, 'AGC',  5, '17:40:00', '17:45:00', 5, 1340),
    (19, 'NDLS', 6, '19:00:00', None, 0, 1535),

    # 20. 12138: Punjab Mail Express (NDLS -> AGC -> GWL -> JHS -> BPL -> CSMT)
    (20, 'NDLS', 1, None, '05:15:00', 0, 0),
    (20, 'AGC',  2, '07:30:00', '07:35:00', 5, 195),
    (20, 'GWL',  3, '09:20:00', '09:25:00', 5, 313),
    (20, 'JHS',  4, '10:45:00', '10:55:00', 10, 410),
    (20, 'BPL',  5, '16:25:00', '16:35:00', 10, 700),
    (20, 'CSMT', 6, '07:35:00', None, 0, 1535),

    # 21. 22436: Vande Bharat (NDLS -> CNB -> PRYJ -> BSB)
    (21, 'NDLS', 1, None, '06:00:00', 0, 0),
    (21, 'CNB',  2, '10:08:00', '10:10:00', 2, 440),
    (21, 'PRYJ', 3, '12:08:00', '12:10:00', 2, 635),
    (21, 'BSB',  4, '14:00:00', None, 0, 755),

    # 22. 22435: Vande Bharat (BSB -> PRYJ -> CNB -> NDLS)
    (22, 'BSB',  1, None, '15:00:00', 0, 0),
    (22, 'PRYJ', 2, '16:30:00', '16:32:00', 2, 120),
    (22, 'CNB',  3, '18:30:00', '18:32:00', 2, 315),
    (22, 'NDLS', 4, '23:00:00', None, 0, 755),

    # 23. 22439: Katra Vande Bharat (NDLS -> CDG -> JAT -> SVDK)
    (23, 'NDLS', 1, None, '06:00:00', 0, 0),
    (23, 'CDG',  2, '08:40:00', '08:42:00', 2, 245),
    (23, 'JAT',  3, '12:38:00', '12:40:00', 2, 580),
    (23, 'SVDK', 4, '14:00:00', None, 0, 655),

    # 24. 22440: Katra Vande Bharat (SVDK -> JAT -> CDG -> NDLS)
    (24, 'SVDK', 1, None, '15:00:00', 0, 0),
    (24, 'JAT',  2, '16:15:00', '16:17:00', 2, 75),
    (24, 'CDG',  3, '20:15:00', '20:17:00', 2, 410),
    (24, 'NDLS', 4, '23:00:00', None, 0, 655),

    # 25. 20901: Vande Bharat Express (BCT -> ST -> BRC -> ADI)
    (25, 'BCT', 1, None, '06:10:00', 0, 0),
    (25, 'ST',  2, '08:50:00', '08:53:00', 3, 265),
    (25, 'BRC', 3, '10:13:00', '10:16:00', 3, 392),
    (25, 'ADI', 4, '11:25:00', None, 0, 492),

    # 26. 20902: Vande Bharat Express (ADI -> BRC -> ST -> BCT)
    (26, 'ADI', 1, None, '15:00:00', 0, 0),
    (26, 'BRC', 2, '16:00:00', '16:03:00', 3, 100),
    (26, 'ST',  3, '17:25:00', '17:28:00', 3, 227),
    (26, 'BCT', 4, '20:25:00', None, 0, 492),

    # 27. 12059: Kota Jan Shatabdi (KOTA -> JP -> NDLS)
    (27, 'KOTA', 1, None, '05:55:00', 0, 0),
    (27, 'JP',   2, '08:30:00', '08:40:00', 10, 240),
    (27, 'NDLS', 3, '12:30:00', None, 0, 465),

    # 28. 12060: Kota Jan Shatabdi (NDLS -> JP -> KOTA)
    (28, 'NDLS', 1, None, '12:45:00', 0, 0),
    (28, 'JP',   2, '16:40:00', '16:50:00', 10, 225),
    (28, 'KOTA', 3, '19:30:00', None, 0, 465),

    # 29. 12414: Pooja Superfast (JAT -> CDG -> JP)
    (29, 'JAT', 1, None, '18:15:00', 0, 0),
    (29, 'CDG', 2, '00:30:00', '00:40:00', 10, 370),
    (29, 'JP',  3, '09:45:00', None, 0, 835),

    # 30. 12413: Pooja Superfast (JP -> CDG -> JAT)
    (30, 'JP',  1, None, '14:10:00', 0, 0),
    (30, 'CDG', 2, '23:15:00', '23:25:00', 10, 465),
    (30, 'JAT', 3, '07:30:00', None, 0, 835)
]

cur.execute("DELETE FROM train_routes")
cur.executemany("""
INSERT INTO train_routes (train_id, station_code, stop_number, arrival_time, departure_time, halt_minutes, distance_km)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", routes)
print(f"✓ Seeded {len(routes)} Comprehensive Intermediate Train Stops.")

# 4. COACHES ACROSS CLASSES (1AC, 2AC, 3AC, SL, CC, EC, 2S)
cur.execute("DELETE FROM train_coaches")
coaches = []
coach_id = 1

for t in trains:
    t_id = t[0]
    t_type = t[3]
    if t_type == 'SHATABDI':
        coaches.append((coach_id, t_id, 'C1', 'CC', 78, 2.10, 450.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'C2', 'CC', 78, 2.10, 450.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'E1', 'EC', 56, 3.50, 950.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'H1', '1AC', 24, 4.50, 1600.00)); coach_id += 1
    elif t_type == 'VANDE_BHARAT':
        coaches.append((coach_id, t_id, 'C1', 'CC', 78, 2.20, 600.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'C2', 'CC', 78, 2.20, 600.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'E1', 'EC', 52, 4.00, 1200.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'H1', '1AC', 24, 4.50, 1700.00)); coach_id += 1
    else:
        coaches.append((coach_id, t_id, 'H1', '1AC', 24, 4.20, 1800.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'A1', '2AC', 46, 2.80, 1100.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'B1', '3AC', 72, 1.90, 750.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'B2', '3AC', 72, 1.90, 750.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'S1', 'SL',  72, 0.80, 320.00)); coach_id += 1
        coaches.append((coach_id, t_id, 'S2', 'SL',  72, 0.80, 320.00)); coach_id += 1

cur.executemany("""
INSERT INTO train_coaches (id, train_id, coach_number, coach_type, total_seats, fare_per_km, base_fare)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", coaches)
print(f"✓ Configured {len(coaches)} Train Coaches across all classes (1AC, 2AC, 3AC, SL, CC, EC).")

# 5. PHYSICAL SEATS
cur.execute("DELETE FROM physical_seats")
seats = []
seat_id = 1
for c in coaches:
    c_id = c[0]
    total_berths = min(c[4], 24) # Seed 24 representative berths per coach
    for s_num in range(1, total_berths + 1):
        b_type = 'LOWER' if s_num % 4 == 1 else 'MIDDLE' if s_num % 4 == 2 else 'UPPER' if s_num % 4 == 3 else 'SIDE_LOWER'
        seats.append((seat_id, c_id, str(s_num), b_type, 1 if s_num % 2 == 1 else 0, (s_num // 8) + 1))
        seat_id += 1

cur.executemany("""
INSERT INTO physical_seats (id, coach_id, seat_number, berth_type, is_window, bay_number)
VALUES (?, ?, ?, ?, ?, ?)
""", seats)
print(f"✓ Generated {len(seats)} Physical Seats.")

# 6. SEAT INVENTORY FOR NEXT 90 DAYS
cur.execute("DELETE FROM seat_inventory")
inventory = []
inv_id = 1
today = datetime.date.today()

for offset in range(90):
    j_date = (today + datetime.timedelta(days=offset)).isoformat()
    for c in coaches:
        c_id = c[0]
        t_id = c[1]
        c_tot = c[4]
        # Realistic varied seat occupancy
        confirmed = (offset * 3 + c_id * 5) % max(1, c_tot - 4)
        avail = max(5, c_tot - confirmed)
        inventory.append((inv_id, t_id, c_id, j_date, c_tot, confirmed, 0, 0, 20, avail))
        inv_id += 1

cur.executemany("""
INSERT INTO seat_inventory (id, train_id, coach_id, journey_date, total_seats, confirmed_count, rac_count, waitlist_count, max_waitlist, available_seats)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", inventory)
print(f"✓ Generated {len(inventory)} Live Seat Inventory Records across 90 days.")

conn.commit()
conn.close()
print("=================================================================")
print(" DATABASE ENRICHMENT COMPLETED SUCCESSFULLY!")
print("=================================================================")
