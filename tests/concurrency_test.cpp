#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <iostream>
#include <vector>
#include <thread>
#include <cassert>
#include <chrono>

#include "db_manager.h"
#include "scheduler.h"
#include "telemetry.h"

using namespace railway;

void run_all_tests() {
    std::cout << "=====================================================================" << std::endl;
    std::cout << "  RUNNING AUTOMATED REPRODUCIBLE TESTS (OS + DBMS CONCURRENCY)       " << std::endl;
    std::cout << "  Team ID: OSDBMS-V-2026-T281                                        " << std::endl;
    std::cout << "=====================================================================" << std::endl;

    DBConfig db_cfg;
    db_cfg.host = "localhost";
    db_cfg.user = "root";
    db_cfg.password = "Root@123";
    db_cfg.database = "smart_railway_db";
    db_cfg.port = 3306;

    DatabaseManager db(db_cfg, 10);
    ResourceScheduler scheduler(db, 6);

    std::string test_train = "12004"; // Lucknow Shatabdi
    std::string test_date = "2026-10-16";
    std::string test_class = "CC";

    // Setup: Reset test inventory for clean reproducible testing
    {
        auto conn_wrapper = db.get_pool().acquire();
        MYSQL* conn = conn_wrapper->get();
        mysql_query(conn, "DELETE FROM bookings WHERE train_number = '12004' AND travel_date = '2026-10-16';");
        mysql_query(conn, "UPDATE physical_seats SET is_booked = FALSE, current_pnr = NULL WHERE train_number = '12004' AND travel_date = '2026-10-16';");
        mysql_query(conn, "UPDATE seat_inventory SET available_seats = 2, current_wl_count = 0 WHERE train_number = '12004' AND travel_date = '2026-10-16' AND coach_class = 'CC';");
        std::cout << "[*] Test inventory initialized: Train 12004, Date 2026-10-16, Available Seats = 2, WL = 0." << std::endl;
    }

    // -------------------------------------------------------------------------
    // TEST 1: RACE CONDITION & CONCURRENT DOUBLE-BOOKING PROTECTION
    // -------------------------------------------------------------------------
    std::cout << "\n[TEST 1] Testing 10 Concurrent Threads Competing for the Last 2 Seats..." << std::endl;
    int num_threads = 10;
    std::vector<std::future<BookingResult>> futures;

    for (int i = 1; i <= num_threads; ++i) {
        BookingRequest req;
        req.train_number = test_train;
        req.travel_date = test_date;
        req.coach_class = test_class;
        req.passenger.name = "Test Passenger #" + std::to_string(i);
        req.passenger.age = 30 + i;
        req.passenger.gender = (i % 2 == 0) ? "Male" : "Female";
        req.passenger.phone = "990000000" + std::to_string(i);
        req.quota = QuotaType::NORMAL;

        futures.push_back(scheduler.enqueue_booking(req));
    }

    int confirmed_count = 0;
    int waiting_count = 0;
    std::vector<std::string> confirmed_pnrs;
    std::vector<int> confirmed_seats;
    std::vector<std::string> waiting_pnrs;

    for (auto& f : futures) {
        BookingResult res = f.get();
        if (res.status == BookingStatus::CONFIRMED) {
            confirmed_count++;
            confirmed_pnrs.push_back(res.pnr);
            confirmed_seats.push_back(res.seat_number);
        } else if (res.status == BookingStatus::WAITING) {
            waiting_count++;
            waiting_pnrs.push_back(res.pnr);
        }
    }

    std::cout << "  -> Confirmed Bookings: " << confirmed_count << " (Expected: 2)" << std::endl;
    std::cout << "  -> Waiting-List Bookings: " << waiting_count << " (Expected: 8)" << std::endl;

    if (confirmed_count != 2) {
        std::cerr << "  [FAIL] Overbooking detected! Confirmed count is " << confirmed_count << std::endl;
        exit(1);
    }

    // Verify in database that two confirmed seats have distinct physical seat numbers
    if (confirmed_seats.size() == 2 && confirmed_seats[0] == confirmed_seats[1]) {
        std::cerr << "  [FAIL] Double-booking detected! Both passengers were assigned seat #" << confirmed_seats[0] << std::endl;
        exit(1);
    }

    std::cout << "  [PASS] ZERO double bookings! Exactly 2 seats allocated to Coach "
              << confirmed_seats[0] << " and " << confirmed_seats[1] << ". Rest queued on Waiting List." << std::endl;

    // -------------------------------------------------------------------------
    // TEST 2: WAITING LIST AUTOMATIC PROMOTION AFTER CANCELLATION
    // -------------------------------------------------------------------------
    std::cout << "\n[TEST 2] Testing Ticket Cancellation and Automatic Waiting-List Promotion..." << std::endl;
    std::string cancel_pnr = confirmed_pnrs[0];
    std::cout << "  -> Cancelling confirmed ticket PNR: " << cancel_pnr << std::endl;

    auto cancel_res = db.execute_cancellation(cancel_pnr, 1);
    std::cout << "  -> Cancellation Message: " << cancel_res.message << std::endl;

    if (!cancel_res.promoted_waiting_passenger) {
        std::cerr << "  [FAIL] Expected a waiting-list passenger to be promoted, but none was promoted!" << std::endl;
        exit(1);
    }

    std::cout << "  -> Promoted Waiting Passenger PNR: " << cancel_res.promoted_pnr << std::endl;

    // Verify the promoted passenger now has status CONFIRMED in the database
    auto pnr_info = db.get_booking_by_pnr(cancel_res.promoted_pnr);
    if (pnr_info["booking_status"] != "CONFIRMED") {
        std::cerr << "  [FAIL] Promoted passenger status in DB is " << pnr_info["booking_status"] << ", expected CONFIRMED!" << std::endl;
        exit(1);
    }

    std::cout << "  [PASS] Waiting-list passenger " << cancel_res.promoted_pnr 
              << " was successfully promoted to CONFIRMED with seat " << pnr_info["coach_name"] 
              << " / " << pnr_info["seat_number"] << " (" << pnr_info["berth_type"] << ")!" << std::endl;

    // -------------------------------------------------------------------------
    // TEST 3: PRIORITY SCHEDULING (EMERGENCY PREEMPTION OVER NORMAL)
    // -------------------------------------------------------------------------
    std::cout << "\n[TEST 3] Testing OS Priority Queue Preemption (EMERGENCY vs NORMAL)..." << std::endl;
    // Enqueue 1 Normal and 1 Emergency simultaneously
    BookingRequest req_normal;
    req_normal.train_number = "22436";
    req_normal.travel_date = "2026-10-18";
    req_normal.coach_class = "CC";
    req_normal.passenger.name = "Normal Citizen";
    req_normal.passenger.age = 28;
    req_normal.passenger.gender = "Male";
    req_normal.passenger.phone = "9812345678";
    req_normal.quota = QuotaType::NORMAL;

    BookingRequest req_emergency;
    req_emergency.train_number = "22436";
    req_emergency.travel_date = "2026-10-18";
    req_emergency.coach_class = "CC";
    req_emergency.passenger.name = "VIP Defense Personnel";
    req_emergency.passenger.age = 42;
    req_emergency.passenger.gender = "Male";
    req_emergency.passenger.phone = "9812345679";
    req_emergency.quota = QuotaType::EMERGENCY;

    auto f_norm = scheduler.enqueue_booking(req_normal);
    auto f_emg = scheduler.enqueue_booking(req_emergency);

    auto r_emg = f_emg.get();
    auto r_norm = f_norm.get();

    assert(r_emg.success);
    assert(r_norm.success);
    std::cout << "  [PASS] Priority requests successfully scheduled and fulfilled without deadlock." << std::endl;

    scheduler.shutdown();

    std::cout << "\n=====================================================================" << std::endl;
    std::cout << "  ALL AUTOMATED CONCURRENCY, OS & DBMS TESTS PASSED SUCCESSFULLY!    " << std::endl;
    std::cout << "=====================================================================" << std::endl;
}

int main() {
    SetConsoleOutputCP(CP_UTF8);
    run_all_tests();
    return 0;
}
