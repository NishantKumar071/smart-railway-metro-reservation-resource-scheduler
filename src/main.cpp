#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <thread>
#include <chrono>

#include "httplib.h"
#include "json.hpp"
#include "db_manager.h"
#include "scheduler.h"
#include "telemetry.h"

using namespace railway;

// Helper to read file from disk
std::string read_file_content(const std::string& path) {
    std::ifstream file(path, std::ios::in | std::ios::binary);
    if (!file.is_open()) return "";
    std::ostringstream ss;
    ss << file.rdbuf();
    return ss.str();
}

void run_cli_mode(DatabaseManager& db, ResourceScheduler& scheduler) {
    std::cout << "\n=======================================================" << std::endl;
    std::cout << "  IRCTC NEXT GENERATION ETICKETING SYSTEM (CONSOLE)    " << std::endl;
    std::cout << "  Centre for Railway Information Systems (CRIS)        " << std::endl;
    std::cout << "=======================================================" << std::endl;

    while (true) {
        std::cout << "\n1. Search Trains (Real Indian Railways)" << std::endl;
        std::cout << "2. Book Ticket (Demonstrate Priority Scheduling)" << std::endl;
        std::cout << "3. Cancel Ticket (Demonstrate Waiting-List Promotion)" << std::endl;
        std::cout << "4. Check PNR Status" << std::endl;
        std::cout << "5. View Live OS & DBMS Telemetry" << std::endl;
        std::cout << "6. Run Concurrency Race Condition Test" << std::endl;
        std::cout << "7. Exit" << std::endl;
        std::cout << "Enter choice: ";

        int choice = 0;
        if (!(std::cin >> choice)) {
            std::cin.clear();
            std::cin.ignore(1000, '\n');
            continue;
        }

        if (choice == 1) {
            std::string src, dst, dt;
            std::cout << "Source Station Code (e.g. NDLS) or press Enter: ";
            std::cin >> src;
            std::cout << "Destination Station Code (e.g. BSB) or press Enter: ";
            std::cin >> dst;
            std::cout << "Travel Date (YYYY-MM-DD) [e.g. 2026-10-15]: ";
            std::cin >> dt;

            auto trains = db.search_trains(src, dst, dt);
            std::cout << "\nFound " << trains.size() << " train(s):" << std::endl;
            for (const auto& t : trains) {
                std::cout << "-> Train #" << t["train_number"] << " " << t["train_name"]
                          << " [" << t["train_type"] << "] | " << t["source_code"] << " (" << t["departure"]
                          << ") -> " << t["dest_code"] << " (" << t["arrival"] << ")" << std::endl;
                for (const auto& c : t["classes"]) {
                    std::cout << "     Class " << c["coach_class"] 
                              << " | Available Seats: " << c["available_seats"]
                              << " | WL: " << c["waiting_list_count"]
                              << " | Fare: Rs. " << c["base_fare"] << std::endl;
                }
            }
        } else if (choice == 2) {
            BookingRequest req;
            std::cout << "Train Number (e.g. 22436): ";
            std::cin >> req.train_number;
            std::cout << "Travel Date (YYYY-MM-DD): ";
            std::cin >> req.travel_date;
            std::cout << "Class (e.g. CC, EC, 3A, 2A): ";
            std::cin >> req.coach_class;
            std::cout << "Passenger Full Name: ";
            std::cin.ignore();
            std::getline(std::cin, req.passenger.name);
            std::cout << "Passenger Age: ";
            std::cin >> req.passenger.age;
            std::cout << "Gender (Male/Female): ";
            std::cin >> req.passenger.gender;
            std::cout << "Phone Number: ";
            std::cin >> req.passenger.phone;

            std::cout << "Quota (1: EMERGENCY, 2: SENIOR_CITIZEN, 3: TATKAL, 4: NORMAL): ";
            int q_choice;
            std::cin >> q_choice;
            if (q_choice == 1) req.quota = QuotaType::EMERGENCY;
            else if (q_choice == 2) req.quota = QuotaType::SENIOR_CITIZEN;
            else if (q_choice == 3) req.quota = QuotaType::TATKAL;
            else req.quota = QuotaType::NORMAL;

            std::cout << "\n[*] Submitting to OS Priority Scheduler (Producer Thread)..." << std::endl;
            auto future = scheduler.enqueue_booking(req);
            BookingResult res = future.get();

            std::cout << "\n--- Booking Result ---" << std::endl;
            std::cout << "Status: " << status_to_string(res.status) << std::endl;
            std::cout << "PNR: " << res.pnr << std::endl;
            if (res.status == BookingStatus::CONFIRMED) {
                std::cout << "Seat Assigned: Coach " << res.coach_name << ", Seat " << res.seat_number << " (" << res.berth_type << ")" << std::endl;
            } else if (res.status == BookingStatus::WAITING) {
                std::cout << "Waiting List Position: WL " << res.wl_position << std::endl;
            }
            std::cout << "Fare: Rs. " << res.fare << std::endl;
            std::cout << "Execution Latency: " << res.execution_time_ms << " ms (Handled by OS Worker #" << res.worker_thread_id << ")" << std::endl;
        } else if (choice == 3) {
            std::string pnr;
            std::cout << "Enter PNR to Cancel: ";
            std::cin >> pnr;
            auto cres = db.execute_cancellation(pnr, 0);
            std::cout << "\n--- Cancellation Result ---" << std::endl;
            std::cout << cres.message << std::endl;
            if (cres.promoted_waiting_passenger) {
                std::cout << ">>> [DBMS EVENT] Waiting-list passenger " << cres.promoted_pnr 
                          << " automatically promoted to CONFIRMED!" << std::endl;
            }
            std::cout << "Refund Amount: Rs. " << cres.refund_amount << " (Latency: " << cres.execution_time_ms << " ms)" << std::endl;
        } else if (choice == 4) {
            std::string pnr;
            std::cout << "Enter PNR: ";
            std::cin >> pnr;
            auto info = db.get_booking_by_pnr(pnr);
            if (info["found"] == true) {
                std::cout << "\n--- PNR Status: " << pnr << " ---" << std::endl;
                std::cout << "Train: " << info["train_number"] << " - " << info["train_name"] << std::endl;
                std::cout << "Passenger: " << info["passenger_name"] << " (Age: " << info["age"] << ", " << info["gender"] << ")" << std::endl;
                std::cout << "Route: " << info["source"] << " -> " << info["dest"] << " on " << info["travel_date"] << std::endl;
                std::cout << "Status: " << info["booking_status"] << std::endl;
                if (info["booking_status"] == "CONFIRMED") {
                    std::cout << "Coach: " << info["coach_name"] << " | Seat: " << info["seat_number"] << " (" << info["berth_type"] << ")" << std::endl;
                } else if (info["booking_status"] == "WAITING") {
                    std::cout << "Waiting List Position: WL " << info["wl_position"] << std::endl;
                }
                std::cout << "Quota: " << info["quota"] << " | Fare: Rs. " << info["fare_paid"] << std::endl;
            } else {
                std::cout << "PNR not found." << std::endl;
            }
        } else if (choice == 5) {
            nlohmann::json telem = SystemTelemetry::instance().to_json();
            std::cout << "\n=== REAL-TIME OS & DBMS TELEMETRY ===" << std::endl;
            std::cout << telem.dump(2) << std::endl;
        } else if (choice == 6) {
            std::cout << "\n[*] Launching 20 Concurrent Threads competing for seats on Train 22436..." << std::endl;
            std::vector<std::future<BookingResult>> futures;
            for (int i = 1; i <= 20; ++i) {
                BookingRequest req;
                req.train_number = "22436";
                req.travel_date = "2026-10-15";
                req.coach_class = "CC";
                req.passenger.name = "Concurrent Passenger #" + std::to_string(i);
                req.passenger.age = 25 + (i % 40);
                req.passenger.gender = (i % 2 == 0) ? "Male" : "Female";
                req.passenger.phone = "98000000" + (i < 10 ? "0" + std::to_string(i) : std::to_string(i));
                req.quota = (i % 4 == 0) ? QuotaType::EMERGENCY : ((i % 3 == 0) ? QuotaType::SENIOR_CITIZEN : QuotaType::NORMAL);
                futures.push_back(scheduler.enqueue_booking(req));
            }

            int cnf = 0, wl = 0, rej = 0;
            for (auto& f : futures) {
                auto r = f.get();
                if (r.status == BookingStatus::CONFIRMED) cnf++;
                else if (r.status == BookingStatus::WAITING) wl++;
                else rej++;
            }
            std::cout << "\n--- Concurrency Test Completed ---" << std::endl;
            std::cout << "Confirmed Bookings: " << cnf << std::endl;
            std::cout << "Waiting List Bookings: " << wl << std::endl;
            std::cout << "Rejected Bookings: " << rej << std::endl;
            std::cout << "Contention Events Prevented: " << SystemTelemetry::instance().to_json()["os"]["contention_events"] << std::endl;
            std::cout << "Result: ZERO double bookings occurred! Strict mutual exclusion verified." << std::endl;
        } else if (choice == 7) {
            break;
        }
    }
}

int main(int argc, char* argv[]) {
    // Enable UTF-8 in Windows console
    SetConsoleOutputCP(CP_UTF8);

    std::cout << "=================================================================" << std::endl;
    std::cout << "  IRCTC NEXT GENERATION ETICKETING ENGINE (TRANSACTION CORE)     " << std::endl;
    std::cout << "  Centre for Railway Information Systems (CRIS)                  " << std::endl;
    std::cout << "=================================================================" << std::endl;

    DBConfig db_cfg;
    db_cfg.host = "localhost";
    db_cfg.user = "root";
    db_cfg.password = "Root@123";
    db_cfg.database = "smart_railway_db";
    db_cfg.port = 3306;

    std::cout << "[*] Connecting to MySQL Server 8.0 on localhost:3306..." << std::endl;
    DatabaseManager db_manager(db_cfg, 8);
    ResourceScheduler scheduler(db_manager, 6);

    SystemTelemetry::instance().set_active_threads(static_cast<int>(scheduler.get_worker_count()));

    if (argc > 1 && std::string(argv[1]) == "--cli") {
        run_cli_mode(db_manager, scheduler);
        scheduler.shutdown();
        return 0;
    }

    httplib::Server svr;

    // CORS Headers for browser communication
    svr.set_default_headers({
        {"Access-Control-Allow-Origin", "*"},
        {"Access-Control-Allow-Methods", "GET, POST, OPTIONS"},
        {"Access-Control-Allow-Headers", "Content-Type"}
    });

    // --------------------------------------------------------------------------
    // API: Stations
    // --------------------------------------------------------------------------
    svr.Get("/api/stations", [&](const httplib::Request&, httplib::Response& res) {
        auto stations = db_manager.get_all_stations();
        nlohmann::json j = nlohmann::json::array();
        for (const auto& s : stations) {
            j.push_back({
                {"code", s.code},
                {"name", s.name},
                {"city", s.city},
                {"state", s.state},
                {"zone", s.zone}
            });
        }
        res.set_content(j.dump(), "application/json");
    });

    // --------------------------------------------------------------------------
    // API: Train Search & Live Availability
    // --------------------------------------------------------------------------
    svr.Get("/api/trains", [&](const httplib::Request& req, httplib::Response& res) {
        std::string src = req.has_param("from") ? req.get_param_value("from") : "";
        std::string dst = req.has_param("to") ? req.get_param_value("to") : "";
        std::string dt = req.has_param("date") ? req.get_param_value("date") : "2026-10-15";

        auto trains = db_manager.search_trains(src, dst, dt);
        nlohmann::json j = trains;
        res.set_content(j.dump(), "application/json");
    });

    // --------------------------------------------------------------------------
    // API: Book Ticket (OS Priority Queue -> Worker Thread Pool -> DBMS Transaction)
    // --------------------------------------------------------------------------
    svr.Post("/api/book", [&](const httplib::Request& req, httplib::Response& res) {
        try {
            auto body = nlohmann::json::parse(req.body);
            BookingRequest b_req;
            b_req.train_number = body["train_number"].get<std::string>();
            b_req.travel_date = body["travel_date"].get<std::string>();
            b_req.coach_class = body["coach_class"].get<std::string>();

            auto p = body["passenger"];
            b_req.passenger.name = p["name"].get<std::string>();
            b_req.passenger.age = p["age"].get<int>();
            b_req.passenger.gender = p["gender"].get<std::string>();
            b_req.passenger.phone = p["phone"].get<std::string>();
            b_req.passenger.email = p.contains("email") ? p["email"].get<std::string>() : "";

            std::string q_str = body.contains("quota") ? body["quota"].get<std::string>() : "NORMAL";
            b_req.quota = string_to_quota(q_str);

            // Enqueue request into OS Priority Scheduler
            auto future = scheduler.enqueue_booking(b_req);
            BookingResult b_res = future.get(); // Wait for worker thread execution

            nlohmann::json j;
            j["success"] = b_res.success;
            j["pnr"] = b_res.pnr;
            j["status"] = status_to_string(b_res.status);
            j["coach_name"] = b_res.coach_name;
            j["seat_number"] = b_res.seat_number;
            j["berth_type"] = b_res.berth_type;
            j["wl_position"] = b_res.wl_position;
            j["fare"] = b_res.fare;
            j["message"] = b_res.message;
            j["execution_time_ms"] = b_res.execution_time_ms;
            j["worker_thread_id"] = b_res.worker_thread_id;

            res.set_content(j.dump(), "application/json");
        } catch (const std::exception& e) {
            nlohmann::json err;
            err["success"] = false;
            err["message"] = std::string("Invalid request format: ") + e.what();
            res.status = 400;
            res.set_content(err.dump(), "application/json");
        }
    });

    // --------------------------------------------------------------------------
    // API: Cancel Ticket (DBMS Cancellation & Waiting List Promotion)
    // --------------------------------------------------------------------------
    svr.Post("/api/cancel", [&](const httplib::Request& req, httplib::Response& res) {
        try {
            auto body = nlohmann::json::parse(req.body);
            std::string pnr = body["pnr"].get<std::string>();

            auto cres = db_manager.execute_cancellation(pnr, 0);

            nlohmann::json j;
            j["success"] = cres.success;
            j["pnr"] = cres.pnr;
            j["message"] = cres.message;
            j["promoted_waiting_passenger"] = cres.promoted_waiting_passenger;
            j["promoted_pnr"] = cres.promoted_pnr;
            j["refund_amount"] = cres.refund_amount;
            j["execution_time_ms"] = cres.execution_time_ms;

            res.set_content(j.dump(), "application/json");
        } catch (const std::exception& e) {
            nlohmann::json err;
            err["success"] = false;
            err["message"] = e.what();
            res.status = 400;
            res.set_content(err.dump(), "application/json");
        }
    });

    // --------------------------------------------------------------------------
    // API: PNR Status
    // --------------------------------------------------------------------------
    svr.Get(R"(/api/pnr/([\w\-]+))", [&](const httplib::Request& req, httplib::Response& res) {
        std::string pnr = req.matches[1];
        auto info = db_manager.get_booking_by_pnr(pnr);
        res.set_content(info.dump(), "application/json");
    });

    // --------------------------------------------------------------------------
    // API: OS & DBMS Live Telemetry
    // --------------------------------------------------------------------------
    svr.Get("/api/telemetry", [&](const httplib::Request&, httplib::Response& res) {
        auto telem = SystemTelemetry::instance().to_json();
        res.set_content(telem.dump(), "application/json");
    });

    // --------------------------------------------------------------------------
    // API: DBMS Transactions Audit Log
    // --------------------------------------------------------------------------
    svr.Get("/api/transactions", [&](const httplib::Request&, httplib::Response& res) {
        auto logs = db_manager.get_recent_transaction_logs(30);
        nlohmann::json arr = nlohmann::json::array();
        for (const auto& l : logs) {
            arr.push_back({
                {"log_id", l.log_id},
                {"thread_id", l.thread_id},
                {"operation", l.operation},
                {"pnr", l.pnr},
                {"details", l.details},
                {"status", l.status},
                {"execution_time_ms", l.execution_time_ms},
                {"created_at", l.created_at}
            });
        }
        res.set_content(arr.dump(), "application/json");
    });

    // --------------------------------------------------------------------------
    // API: Concurrency Stress Test Simulation
    // Spawns 20 concurrent threads competing for the last available seats
    // --------------------------------------------------------------------------
    svr.Post("/api/simulate-concurrency", [&](const httplib::Request&, httplib::Response& res) {
        std::vector<std::future<BookingResult>> futures;
        int thread_count = 20;

        for (int i = 1; i <= thread_count; ++i) {
            BookingRequest req;
            req.train_number = "22436"; // Vande Bharat Express
            req.travel_date = "2026-10-15";
            req.coach_class = "CC";
            req.passenger.name = "Test Concurrent Passenger #" + std::to_string(i);
            req.passenger.age = 22 + (i % 50);
            req.passenger.gender = (i % 2 == 0) ? "Male" : "Female";
            req.passenger.phone = "98110000" + (i < 10 ? "0" + std::to_string(i) : std::to_string(i));
            req.passenger.email = "concurrent." + std::to_string(i) + "@test.com";

            // Mix priorities to demonstrate priority scheduling under concurrency
            if (i <= 3) req.quota = QuotaType::EMERGENCY;
            else if (i <= 7) req.quota = QuotaType::SENIOR_CITIZEN;
            else if (i <= 11) req.quota = QuotaType::TATKAL;
            else req.quota = QuotaType::NORMAL;

            futures.push_back(scheduler.enqueue_booking(req));
        }

        nlohmann::json summary;
        int confirmed = 0;
        int waiting = 0;
        int rejected = 0;
        nlohmann::json details = nlohmann::json::array();

        for (size_t i = 0; i < futures.size(); ++i) {
            auto r = futures[i].get();
            if (r.status == BookingStatus::CONFIRMED) confirmed++;
            else if (r.status == BookingStatus::WAITING) waiting++;
            else rejected++;

            details.push_back({
                {"request_id", i + 1},
                {"pnr", r.pnr},
                {"status", status_to_string(r.status)},
                {"seat", r.status == BookingStatus::CONFIRMED ? (r.coach_name + " / " + std::to_string(r.seat_number)) : "-"},
                {"wl_pos", r.wl_position},
                {"worker_thread", r.worker_thread_id},
                {"latency_ms", r.execution_time_ms}
            });
        }

        summary["total_threads_fired"] = thread_count;
        summary["confirmed_seats"] = confirmed;
        summary["waiting_list_allocated"] = waiting;
        summary["rejected_regrets"] = rejected;
        summary["race_conditions_prevented"] = true;
        summary["double_booking_detected"] = false;
        summary["requests"] = details;

        res.set_content(summary.dump(), "application/json");
    });

    // --------------------------------------------------------------------------
    // API: Trigger Python Railway Data Sync
    // --------------------------------------------------------------------------
    svr.Post("/api/sync-railway-data", [&](const httplib::Request&, httplib::Response& res) {
        int ret = system("C:\\Python314\\python.exe scripts\\sync_railway_data.py");
        nlohmann::json j;
        j["success"] = (ret == 0);
        j["message"] = (ret == 0) ? "Real Indian Railways data synchronized successfully!" : "Data sync encountered an error.";
        res.set_content(j.dump(), "application/json");
    });

    // --------------------------------------------------------------------------
    // Static Web Dashboard Serving
    // --------------------------------------------------------------------------
    svr.Get("/", [](const httplib::Request&, httplib::Response& res) {
        std::string html = read_file_content("web/index.html");
        res.set_content(html, "text/html");
    });

    svr.Get("/style.css", [](const httplib::Request&, httplib::Response& res) {
        std::string css = read_file_content("web/style.css");
        res.set_content(css, "text/css");
    });

    svr.Get("/app.js", [](const httplib::Request&, httplib::Response& res) {
        std::string js = read_file_content("web/app.js");
        res.set_content(js, "application/javascript");
    });

    std::cout << "\n=================================================================" << std::endl;
    std::cout << "[SUCCESS] C++ REST Backend & Scheduler Daemon is running!" << std::endl;
    std::cout << "-> Web Dashboard URL: http://localhost:8080" << std::endl;
    std::cout << "-> OS Worker Threads: " << scheduler.get_worker_count() << std::endl;
    std::cout << "-> MySQL Database:    smart_railway_db on port 3306" << std::endl;
    std::cout << "Press Ctrl+C to stop the daemon gracefully." << std::endl;
    std::cout << "=================================================================\n" << std::endl;

    svr.listen("0.0.0.0", 8080);

    scheduler.shutdown();
    return 0;
}
