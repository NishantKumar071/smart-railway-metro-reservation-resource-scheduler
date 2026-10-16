# Smart Railway Reservation & Resource Scheduler (OS + DBMS)

[![University Project](https://img.shields.io/badge/Project-OS%20%2B%20DBMS%20Capstone-blue.svg)](https://github.com/)
[![C++17 Standard](https://img.shields.io/badge/Language-C%2B%2B17-00599C.svg?logo=c%2B%2B)](https://isocpp.org/)
[![MySQL 8.0](https://img.shields.io/badge/Database-MySQL%208.0.46-4479A1.svg?logo=mysql)](https://www.mysql.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-0078D6.svg?logo=windows)](https://microsoft.com/)

---

## 🎓 Academic Project Information
- **Project Title:** Smart Railway Reservation & Resource Scheduler
- **Team ID:** `OSDBMS-V-2026-T281`
- **Domain:** Operating Systems (OS) + Database Management Systems (DBMS)
- **Team Leader:** Nishant Kumar
- **Team Member:** Robert Sandi Thomas
- **Target Environment:** Windows 10/11 x64, Visual Studio 2022 / MSVC x64, MySQL Server 8.0.46, Python 3.14

---

## 📌 Executive Summary
High-traffic railway ticketing engines (such as Indian Railways IRCTC) face intense concurrency during tatkal hours, where thousands of booking requests hit the server within milliseconds for a handful of seats.

This project delivers a **native C++ multi-threaded reservation system backed by MySQL Server 8.0**, strictly adhering to core Operating Systems scheduling and DBMS transaction safety principles:
1. **Producer-Consumer Architecture:** Incoming booking requests are enqueued into a synchronized priority queue.
2. **Priority Task Scheduling:** Requests are scheduled by quota precedence:
   - **Priority 1 (Highest):** `EMERGENCY` (VIP / Defense / Medical emergency quota)
   - **Priority 2:** `SENIOR_CITIZEN` (Age &ge; 60 lower berth priority with concession)
   - **Priority 3:** `TATKAL` (Premium last-minute reservation)
   - **Priority 4 (Lowest):** `NORMAL` (General public FCFS)
3. **Mutual Exclusion & Concurrency Control:** Fine-grained per-train mutexes and `SELECT ... FOR UPDATE` row locks eliminate race conditions and mathematically prevent double-booking.
4. **ACID Transactions & Automated Waiting-List (WL) Promotion:** When a confirmed seat is cancelled, an atomic transaction reallocates the seat to the highest-priority waiting-list passenger, updates the physical seat berth, and commits atomically.
5. **Real Indian Railways Integration:** Built-in verified timetables (Vande Bharat Express, Mumbai Rajdhani, Howrah Rajdhani, Shatabdi Express) and an automated updater service (`scripts/sync_railway_data.py`) syncing schedules from open datasets.
6. **Built-in Web Dashboard & Live OS/DBMS Telemetry:** Native C++ HTTP daemon serving a real-time IRCTC-themed dashboard displaying thread pool states, queue depths, mutex contention counters, and transaction audit logs.

---

## 🏗️ System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                       FRONTEND DASHBOARD                                          |
|  - Modern IRCTC Theme (HTML5, CSS, Vanilla JS)                                                    |
|  - Real Indian Railways Search (NDLS, MMCT, HWH, MAS, SBC, BSB, LKO, PUNE, ADI, TVC)              |
|  - Quota Selection (Emergency / Senior Citizen / Tatkal / General)                                |
|  - Real-Time OS & DBMS Telemetry Panel & 1-Click Concurrency Stress Test                         |
+-------------------------------------------------+-------------------------------------------------+
                                                  | HTTP REST / JSON (Port 8080)
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                C++ CORE SCHEDULER & BOOKING DAEMON                                |
|                                                                                                   |
|  [cpp-httplib REST Server (Port 8080)]                                                            |
|         |                                                                                         |
|         v (Producer enqueues BookingRequest)                                                      |
|  +---------------------------------------------------------------------------------------------+  |
|  | [OS Concept: Synchronized Priority Request Queue]                                           |  |
|  | - Priority 1: EMERGENCY (VIP / Defense / Medical)                                           |  |
|  | - Priority 2: SENIOR CITIZEN (Age >= 60)                                                    |  |
|  | - Priority 3: TATKAL (Last minute reservation)                                              |  |
|  | - Priority 4: NORMAL (General public)                                                       |  |
|  | - std::priority_queue protected by std::mutex & std::condition_variable                     |  |
|  +---------------------------------------------------------------------------------------------+  |
|         | (Consumer threads pick highest priority requests)                                       |
|         v                                                                                         |
|  +---------------------------------------------------------------------------------------------+  |
|  | [OS Concept: Worker Thread Pool (6 Concurrent OS Threads)]                                  |  |
|  | - Dispatches booking, cancellation, and simulation tasks concurrently                       |  |
|  | - Fine-grained per-train mutexes preventing race conditions & double-booking                |  |
|  | - OS Telemetry: active workers, queue wait time, lock acquisition contention counter        |  |
|  +---------------------------------------------------------------------------------------------+  |
|         | Native MySQL C API (mysql.h / libmysql.lib)                                             |
|         v                                                                                         |
|  +---------------------------------------------------------------------------------------------+  |
|  | [DBMS Manager: Transaction & Concurrency Control]                                           |  |
|  | - BEGIN TRANSACTION ... COMMIT / ROLLBACK                                                   |  |
|  | - SELECT ... FOR UPDATE (Row-level pessimistic locking on coach & seat inventory)           |  |
|  | - Automatic Waiting-List allocation when seats reach 0                                      |  |
|  | - Cancellation workflow: Releases seat -> Promotes top WL passenger -> commits atomically   |  |
|  | - Audit Trail: Logs all transactions (thread ID, status, execution duration in ms)          |  |
|  +---------------------------------------------------------------------------------------------+  |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                       MySQL SERVER 8.0                                            |
|  - Database: `smart_railway_db`                                                                  |
|  - InnoDB tables: stations, trains, train_coaches, seat_inventory, physical_seats, passengers,     |
|    bookings, db_transactions_log, os_scheduling_metrics                                           |
|  - Composite Unique Constraints: (train_id, travel_date, coach_name, seat_number)                 |
+-------------------------------------------------+-------------------------------------------------+
                                                  ^
                                                  | Automated / Scheduled Sync
+-------------------------------------------------+-------------------------------------------------+
|                       REAL INDIAN RAILWAYS DATA & AUTO-UPDATER                                    |
|  - Seed Data: Real Indian Railway routes (Vande Bharat, Rajdhani, Shatabdi, Superfast)            |
|  - Auto-Updater Script (`scripts/sync_railway_data.py`):                                          |
|    Fetches updated station schedules / route modifications from public Indian Railway datasets     |
|    (DataMeet / NTES public routes) and upserts them into MySQL.                                   |
+---------------------------------------------------------------------------------------------------+
```

---

## 🔬 Operating Systems (OS) Concepts Mapping

| Concept | Concrete Implementation in Code |
| :--- | :--- |
| **Producer-Consumer Pattern** | The web server / client threads act as *Producers* pushing `BookingRequest` structs into a bounded buffer. A pool of *Consumer* worker threads blocks on `std::condition_variable` and processes requests when notified (`src/scheduler.cpp`). |
| **Priority Task Scheduling** | `std::priority_queue` with custom comparator `BookingPriorityComparator` orders requests by `(priority_level, timestamp)`. Emergency requests preempt general requests in the queue (`include/models.h`). |
| **Mutual Exclusion & Concurrency** | Dedicated `std::mutex` instances protect the queue and individual train resources. Multiple worker threads can book seats on different trains concurrently, but requests on the same train are safely serialized. |
| **Contention & Telemetry Tracking** | The scheduler attempts `try_lock()`. If a lock is contended, it increments the OS contention event counter before blocking, visibly proving race-condition resolution on the dashboard (`src/telemetry.cpp`). |
| **Deadlock Avoidance** | Strict global lock hierarchy protocol: `Queue Lock -> Train Mutex -> DB Connection Pool Lock`. Locks are acquired and released using RAII (`std::unique_lock` / `std::lock_guard`). |

---

## 🗄️ Database Management Systems (DBMS) Concepts Mapping

| Concept | Concrete Implementation in Code |
| :--- | :--- |
| **ACID Transactions** | Every reservation and cancellation executes inside an explicit `START TRANSACTION ... COMMIT` block. If capacity is exhausted or an error occurs, an immediate `ROLLBACK` is triggered (`src/db_manager.cpp`). |
| **Pessimistic Row-Level Locking** | `SELECT ... FOR UPDATE` locks the seat inventory row during availability checks, preventing lost updates and dirty reads under high concurrency. |
| **Waiting List (WL) Promotion** | When a confirmed ticket is cancelled, an atomic transaction queries the waiting list ordered by `priority_level ASC, wl_position ASC LIMIT 1 FOR UPDATE`, reallocates the physical seat, promotes the passenger, and commits atomically. |
| **Relational Integrity & Constraints** | Foreign keys with `CASCADE` and `RESTRICT` rules, `CHECK` constraints on age ranges, and a composite `UNIQUE KEY (train_number, travel_date, coach_name, seat_number)` preventing double allocation at the physical DB level. |
| **Audit Logging & Indexing** | Every database transaction is permanently logged into `db_transactions_log` with execution duration, thread ID, and status (`COMMITTED` / `ROLLEDBACK`). B-Tree indexes speed up route searching and waiting-list lookups. |

---

## 🚆 Real Indian Railways Dataset & Route Sync

The system includes real trains and stations:
- **Train 22436 / 22435:** New Delhi (`NDLS`) &harr; Varanasi (`BSB`) Vande Bharat Express (759 km)
- **Train 12952 / 12951:** New Delhi (`NDLS`) &harr; Mumbai Central (`MMCT`) Mumbai Rajdhani (1386 km)
- **Train 12302:** New Delhi (`NDLS`) &rarr; Howrah Jn (`HWH`) Kolkata Rajdhani (1451 km)
- **Train 12004:** New Delhi (`NDLS`) &rarr; Lucknow Charbagh (`LKO`) Shatabdi Express (513 km)
- **Train 20608 / 20607:** KSR Bengaluru (`SBC`) &harr; MGR Chennai Central (`MAS`) Vande Bharat (359 km)
- **Train 12626:** New Delhi (`NDLS`) &rarr; Trivandrum Central (`TVC`) Kerala Express (3036 km)
- **Train 12124:** Pune Jn (`PUNE`) &rarr; Mumbai Central (`MMCT`) Deccan Queen (192 km)
- **Train 12932:** Ahmedabad (`ADI`) &rarr; Mumbai Central (`MMCT`) AC Double Decker (491 km)

### Automated Route & Timetable Updater (`scripts/sync_railway_data.py`)
- Pulls live route schedules and station coordinates from public Indian Railways repositories (DataMeet / IRCTC open formats).
- Performs upserts (`INSERT ... ON DUPLICATE KEY UPDATE`) into MySQL.
- Can be run on demand via the Web Dashboard or in daemon mode:
  ```powershell
  python scripts\sync_railway_data.py --daemon --interval 3600
  ```

---

## 📂 Project Directory Structure

```
smartrailwayproject/
├── build.bat                  # One-click compile script using MSVC x64
├── run.bat                    # One-click launch script for Web Server + Browser
├── run_cli.bat                # Interactive terminal CLI mode (for viva/grading)
├── test.bat                   # Executes automated concurrency test suite
├── CMakeLists.txt             # Cross-platform CMake configuration
├── README.md                  # Comprehensive academic report & setup guide
├── .gitignore                 # Git ignore rules
├── include/                   # C++ Header files
│   ├── httplib.h              # Embedded C++ HTTP server
│   ├── json.hpp               # JSON for Modern C++ (nlohmann)
│   ├── models.h               # Data models, Quota enums, Comparators
│   ├── telemetry.h            # Real-time OS/DBMS telemetry counters
│   ├── db_manager.h           # MySQL C API wrapper & connection pool
│   └── scheduler.h            # Priority queue & thread pool scheduler
├── src/                       # C++ Source implementations
│   ├── main.cpp               # Server entry, REST endpoints, CLI runner
│   ├── db_manager.cpp         # ACID transactions, row locking, WL promotion
│   ├── scheduler.cpp          # Worker threads, priority dispatching, mutexes
│   └── telemetry.cpp          # Metric trackers
├── tests/                     # Automated reproducible tests
│   └── concurrency_test.cpp   # Race condition, WL promotion, and priority tests
├── sql/
│   ├── schema.sql             # Relational DDL with InnoDB, FKs, indexes
│   ├── seed_real_data.sql     # Real Indian Railways trains & 14-day inventories
│   └── setup_database.bat     # One-click database initializer
├── scripts/
│   └── sync_railway_data.py   # Real Indian Railways schedule synchronizer
└── web/                       # Frontend Web Dashboard (served directly by C++)
    ├── index.html             # IRCTC themed responsive interface
    ├── style.css              # Custom styling & telemetry badges
    └── app.js                 # AJAX polling, booking workflow, stress test
```

---

## 🚀 Quick Start Guide (Windows)

### Prerequisites
1. **Windows 10/11 x64**
2. **Visual Studio 2022 / Build Tools** (C++ x64 compiler `cl.exe`)
3. **MySQL Server 8.0.46** running on port 3306
4. **Python 3.10+** (with `pymysql` installed)

### Step 1: Initialize Database
Run the setup batch script or execute the SQL files in MySQL Workbench:
```cmd
sql\setup_database.bat
```
*(Default credentials configured: `root` / `Root@123` on `localhost:3306`).*

### Step 2: Compile the Project
Run the automated build script:
```cmd
build.bat
```
This compiles `smart_railway.exe` (main server) and `concurrency_test.exe` (test suite) using MSVC x64 and automatically copies `libmysql.dll`.

### Step 3: Run Automated Concurrency Tests
Verify race condition protection and waiting list promotions:
```cmd
test.bat
```
**Expected Test Output:**
```
[TEST 1] Testing 10 Concurrent Threads Competing for the Last 2 Seats...
  -> Confirmed Bookings: 2 (Expected: 2)
  -> Waiting-List Bookings: 8 (Expected: 8)
  [PASS] ZERO double bookings! Exactly 2 seats allocated to Coach 1 and 2. Rest queued on Waiting List.

[TEST 2] Testing Ticket Cancellation and Automatic Waiting-List Promotion...
  -> Cancelling confirmed ticket PNR: 296-0287195
  -> Cancellation Message: Ticket cancelled. Waiting-list passenger 539-7575426 was automatically promoted to CONFIRMED!
  [PASS] Waiting-list passenger was successfully promoted to CONFIRMED!

[TEST 3] Testing OS Priority Queue Preemption (EMERGENCY vs NORMAL)...
  [PASS] Priority requests successfully scheduled and fulfilled without deadlock.
```

### Step 4: Launch Web Dashboard
Start the C++ web server and open the browser:
```cmd
run.bat
```
Open **[http://localhost:8080](http://localhost:8080)** in any browser.

### Step 5: Interactive Terminal CLI Mode (For Viva Examination)
If your professors ask to inspect or test the program in a console window:
```cmd
run_cli.bat
```

---

## 🎯 Viva Q&A Guide (For University Evaluators)

**Q1: How do you prevent double booking when 100 passengers book the last seat simultaneously?**
> **Answer:** We employ two complementary layers of defense:
> 1. *Operating System Level:* In `ResourceScheduler`, each train has an associated `std::mutex`. When worker threads consume requests for a specific train, only one thread can hold that train's mutex at any instant, serializing concurrent writes.
> 2. *DBMS Level:* Inside the transaction, we issue `SELECT available_seats FROM seat_inventory WHERE ... FOR UPDATE`. This places an exclusive row-level lock in MySQL InnoDB. If available seats equal zero, subsequent requests are automatically moved to the Waiting List or rolled back. Furthermore, a composite `UNIQUE KEY (train_number, travel_date, coach_name, seat_number)` guarantees at the database storage engine that two confirmed bookings can never share the same seat.

**Q2: How is priority scheduling implemented?**
> **Answer:** In `scheduler.cpp`, we utilize a bounded `std::priority_queue` guarded by a `std::mutex` and `std::condition_variable`. We defined a custom comparator `BookingPriorityComparator` where `EMERGENCY` is Priority 1, `SENIOR_CITIZEN` is Priority 2, `TATKAL` is Priority 3, and `NORMAL` is Priority 4. Whenever a worker thread dequeues a task, the heap property guarantees that Emergency and Senior Citizen requests are dispatched ahead of General requests, regardless of when they arrived.

**Q3: How does the waiting list promotion transaction work during ticket cancellation?**
> **Answer:** In `DatabaseManager::execute_cancellation()`, cancellation and promotion occur within an atomic `START TRANSACTION ... COMMIT` boundary:
> 1. The target booking row is locked and marked `CANCELLED`.
> 2. A query searches for the top waiting list passenger: `SELECT booking_id FROM bookings WHERE booking_status = 'WAITING' ORDER BY priority_level ASC, wl_position ASC LIMIT 1 FOR UPDATE`.
> 3. If a waiting passenger exists, their status is updated to `CONFIRMED`, the freed physical seat is assigned to them, and the waiting list count is decremented.
> 4. If any step fails, the entire transaction issues a `ROLLBACK`, guaranteeing zero orphan records or inconsistent inventory states.

---

## 👥 Contributors
- **Nishant Kumar** (Team Leader)
- **Robert Sandi Thomas** (Team Member)
- **University Project ID:** `OSDBMS-V-2026-T281`
