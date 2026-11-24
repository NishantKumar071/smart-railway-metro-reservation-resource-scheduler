#include "booking_engine.h"
#include <random>
#include <sstream>
#include <iomanip>
#include <mutex>
#include <unordered_map>
#include <iostream>

namespace smartrail {

// In-memory atomic inventory simulating MySQL row-level locking
static std::mutex g_inventory_mutex;
static std::unordered_map<std::string, int> g_train_available_seats = {
    {"12301_B1", 8},
    {"12017_C1", 24},
    {"12951_B1", 12},
    {"CONCURRENCY_TEST_COACH", 2} // Specifically set to 2 seats for concurrency verification!
};
static std::unordered_map<std::string, int> g_train_waitlist_counts;

BookingEngine& BookingEngine::instance() {
    static BookingEngine inst;
    return inst;
}

std::string BookingEngine::generate_unique_pnr() {
    static std::random_device rd;
    static std::mt19937_64 gen(rd());
    static std::uniform_int_distribution<long long> dis(1000000000LL, 9999999999LL);
    return std::to_string(dis(gen));
}

BookingResult BookingEngine::process_booking(const BookingRequestData& req, int worker_id) {
    BookingResult result;
    result.pnr = generate_unique_pnr();
    result.coach_number = req.coach_number.empty() ? "B1" : req.coach_number;
    result.total_fare = req.total_fare;
    result.worker_thread_id = worker_id;

    std::string inv_key = req.coach_number.empty() ? "12301_B1" : req.coach_number;

    // Simulate DBMS SELECT FOR UPDATE and atomic commit/rollback
    {
        std::lock_guard<std::mutex> lock(g_inventory_mutex);
        int available = g_train_available_seats[inv_key];

        if (available > 0) {
            // Allocate confirmed seat
            g_train_available_seats[inv_key] = available - 1;
            result.success = true;
            result.booking_status = "CONFIRMED";
            result.seat_number = std::to_string(73 - available);
            result.berth_allotted = (req.preferred_berth != "NO_PREFERENCE") ? req.preferred_berth : "LOWER";
            result.message = "Booking confirmed successfully.";
        } else {
            // Place into waiting list
            int wl = ++g_train_waitlist_counts[inv_key];
            result.success = true;
            result.booking_status = "WAITING";
            result.waitlist_number = wl;
            result.message = "Seats full. Placed on waiting list (WL " + std::to_string(wl) + ").";
        }
    }

    return result;
}

bool BookingEngine::cancel_booking(const std::string& pnr, std::string& out_promoted_pnr) {
    std::lock_guard<std::mutex> lock(g_inventory_mutex);
    out_promoted_pnr = "";
    (void)pnr;
    return true;
}

} // namespace smartrail
