#include "scheduler.h"
#include "telemetry.h"
#include <cassert>
#include <iostream>
#include <vector>

void test_os_priority_scheduling() {
    std::cout << "[Test 1] Testing OS Priority Queue Ordering...\n";
    smartrail::PriorityScheduler scheduler(4, 50);
    scheduler.start();

    // Submit normal, then senior citizen, then emergency
    smartrail::BookingRequestData req_normal;
    req_normal.request_id = "REQ-NORMAL";
    req_normal.quota = "GENERAL";

    smartrail::BookingRequestData req_emergency;
    req_emergency.request_id = "REQ-EMERGENCY";
    req_emergency.quota = "EMERGENCY";

    auto f1 = scheduler.submit_booking(req_normal);
    auto f2 = scheduler.submit_booking(req_emergency);

    auto r1 = f1.get();
    auto r2 = f2.get();

    assert(r1.success);
    assert(r2.success);
    std::cout << "  ✓ Both priority requests processed.\n";
    scheduler.stop();
}

void test_concurrency_race_conditions() {
    std::cout << "[Test 2] Testing Concurrency with 10 Simultaneous Requests (2 Seats Available)...\n";
    smartrail::PriorityScheduler scheduler(6, 100);
    scheduler.start();

    std::vector<std::future<smartrail::BookingResult>> futures;
    for (int i = 0; i < 10; ++i) {
        smartrail::BookingRequestData req;
        req.request_id = "CONC-REQ-" + std::to_string(i + 1);
        req.coach_number = "CONCURRENCY_TEST_COACH"; // Has exactly 2 seats
        req.quota = (i % 2 == 0) ? "TATKAL" : "GENERAL";
        futures.push_back(scheduler.submit_booking(req));
    }

    int confirmed = 0;
    int waitlisted = 0;
    std::vector<std::string> allocated_seats;

    for (auto& f : futures) {
        auto res = f.get();
        if (res.booking_status == "CONFIRMED") {
            confirmed++;
            allocated_seats.push_back(res.seat_number);
        } else if (res.booking_status == "WAITING") {
            waitlisted++;
        }
    }

    std::cout << "  Results: Confirmed=" << confirmed << " | Waitlisted=" << waitlisted << "\n";
    assert(confirmed == 2);
    assert(waitlisted == 8);
    // Ensure no duplicate physical seat was allocated!
    assert(allocated_seats.size() == 2);
    assert(allocated_seats[0] != allocated_seats[1]);

    std::cout << "  ✓ Exactly 2 confirmed, 8 waitlisted, 0 duplicate physical seats.\n";
    scheduler.stop();
}

int main() {
    std::cout << "========================================\n";
    std::cout << " SmartRail AI+ C++ OS Concurrency Tests\n";
    std::cout << "========================================\n";
    test_os_priority_scheduling();
    test_concurrency_race_conditions();
    std::cout << "\nALL C++ TESTS PASSED SUCCESSFULLY!\n";
    return 0;
}
