#include "config.h"
#include "scheduler.h"
#include "telemetry.h"
#include "booking_engine.h"
#include <iostream>
#include <chrono>
#include <thread>

int main(int argc, char* argv[]) {
    std::cout << "===============================================================\n";
    std::cout << " SmartRail AI+ — C++ High-Performance Booking & Scheduling Engine\n";
    std::cout << " Graphic Era (Deemed to be University), Dehradun\n";
    std::cout << " Team: OSDBMS-V-2026-T281\n";
    std::cout << "===============================================================\n";

    smartrail::Config config;
    if (argc > 1) {
        config.server_port = std::stoi(argv[1]);
    }

    std::cout << "[Init] Initializing OS Priority Scheduler with "
              << config.worker_threads << " worker threads...\n";

    smartrail::PriorityScheduler scheduler(config.worker_threads, config.max_queue_size);
    scheduler.start();

    std::cout << "[Init] C++ Booking Engine is active.\n";
    std::cout << "[Init] Telemetry tracking enabled.\n";
    std::cout << "[Ready] Accepting booking requests across threads.\n";

    // Demo automated execution to verify thread scheduling
    smartrail::BookingRequestData sample_req;
    sample_req.request_id = "INIT-REQ-001";
    sample_req.coach_number = "12301_B1";
    sample_req.quota = "TATKAL";
    sample_req.total_fare = 1245.0;

    auto future = scheduler.submit_booking(sample_req);
    auto res = future.get();

    std::cout << "[Verification] Sample Request processed by Worker Thread #"
              << res.worker_thread_id << " -> PNR: " << res.pnr
              << " | Status: " << res.booking_status
              << " | Seat: " << res.seat_number << "\n";

    std::cout << "[Notice] Standalone C++ engine initialized successfully.\n";
    std::cout << "Press Ctrl+C to terminate or keep running for benchmark...\n";

    // Keep active for background processing
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    scheduler.stop();

    return 0;
}
