#include "db_manager.h"
#include "telemetry.h"
#include <iostream>
#include <sstream>
#include <random>
#include <iomanip>
#include <chrono>

namespace railway {

// ------------------------------------------------------------------------------
// ScopedConnection RAII Implementation
// ------------------------------------------------------------------------------
ScopedConnection::ScopedConnection(DBConnectionPool& pool, MYSQL* conn)
    : pool_(pool), conn_(conn) {}

ScopedConnection::~ScopedConnection() {
    if (conn_) {
        pool_.release(conn_);
    }
}

// ------------------------------------------------------------------------------
// DBConnectionPool Implementation
// ------------------------------------------------------------------------------
DBConnectionPool::DBConnectionPool(const DBConfig& config, size_t pool_size)
    : config_(config), pool_size_(pool_size) {
    for (size_t i = 0; i < pool_size_; ++i) {
        MYSQL* conn = create_connection();
        if (conn) {
            pool_.push(conn);
        } else {
            std::cerr << "[DBConnectionPool] Warning: Failed to initialize MySQL connection #" << i << std::endl;
        }
    }
    std::cout << "[DBConnectionPool] Initialized pool with " << pool_.size() << " active connections." << std::endl;
}

DBConnectionPool::~DBConnectionPool() {
    std::unique_lock<std::mutex> lock(mutex_);
    stopped_ = true;
    while (!pool_.empty()) {
        MYSQL* conn = pool_.front();
        pool_.pop();
        if (conn) {
            mysql_close(conn);
        }
    }
}

MYSQL* DBConnectionPool::create_connection() {
    MYSQL* conn = mysql_init(nullptr);
    if (!conn) {
        std::cerr << "[DBConnectionPool] mysql_init failed!" << std::endl;
        return nullptr;
    }

    bool reconnect = true;
    mysql_options(conn, MYSQL_OPT_RECONNECT, &reconnect);

    if (!mysql_real_connect(conn, config_.host.c_str(), config_.user.c_str(),
                           config_.password.c_str(), config_.database.c_str(),
                           config_.port, nullptr, CLIENT_MULTI_STATEMENTS)) {
        std::cerr << "[DBConnectionPool] mysql_real_connect failed: " << mysql_error(conn) << std::endl;
        mysql_close(conn);
        return nullptr;
    }

    // Set UTF-8
    mysql_set_character_set(conn, "utf8mb4");
    return conn;
}

std::unique_ptr<ScopedConnection> DBConnectionPool::acquire() {
    std::unique_lock<std::mutex> lock(mutex_);
    cv_.wait(lock, [this]() { return stopped_ || !pool_.empty(); });

    if (stopped_ || pool_.empty()) {
        return nullptr;
    }

    MYSQL* conn = pool_.front();
    pool_.pop();

    // Ping to verify connection is alive
    if (mysql_ping(conn) != 0) {
        mysql_close(conn);
        conn = create_connection();
    }

    return std::make_unique<ScopedConnection>(*this, conn);
}

void DBConnectionPool::release(MYSQL* conn) {
    std::unique_lock<std::mutex> lock(mutex_);
    if (!stopped_ && conn) {
        pool_.push(conn);
        lock.unlock();
        cv_.notify_one();
    } else if (conn) {
        mysql_close(conn);
    }
}

// ------------------------------------------------------------------------------
// DatabaseManager Implementation
// ------------------------------------------------------------------------------
DatabaseManager::DatabaseManager(const DBConfig& config, size_t pool_size)
    : config_(config), pool_(config, pool_size) {}

std::string DatabaseManager::escape_string(MYSQL* conn, const std::string& str) {
    std::vector<char> buffer(str.length() * 2 + 1);
    mysql_real_escape_string(conn, buffer.data(), str.c_str(), static_cast<unsigned long>(str.length()));
    return std::string(buffer.data());
}

std::string DatabaseManager::generate_pnr() {
    static std::random_device rd;
    static std::mt19937_64 gen(rd());
    static std::uniform_int_distribution<long long> dis(1000000000LL, 9999999999LL);
    
    long long num = dis(gen);
    std::string s = std::to_string(num);
    return s.substr(0, 3) + "-" + s.substr(3);
}

void DatabaseManager::log_transaction(int thread_id, const std::string& op, const std::string& pnr, 
                                     const std::string& details, const std::string& status, double duration_ms) {
    auto conn_wrapper = pool_.acquire();
    if (!conn_wrapper) return;
    MYSQL* conn = conn_wrapper->get();

    std::string esc_op = escape_string(conn, op);
    std::string esc_pnr = escape_string(conn, pnr);
    std::string esc_det = escape_string(conn, details);
    std::string esc_st = escape_string(conn, status);

    std::ostringstream ss;
    ss << "INSERT INTO db_transactions_log (thread_id, operation, pnr, details, status, execution_time_ms) "
       << "VALUES (" << thread_id << ", '" << esc_op << "', "
       << (pnr.empty() ? "NULL" : ("'" + esc_pnr + "'")) << ", '"
       << esc_det << "', '" << esc_st << "', " << duration_ms << ");";

    mysql_query(conn, ss.str().c_str());
}

std::vector<Station> DatabaseManager::get_all_stations() {
    std::vector<Station> list;
    auto conn_wrapper = pool_.acquire();
    if (!conn_wrapper) return list;
    MYSQL* conn = conn_wrapper->get();

    std::string sql = "SELECT station_code, station_name, city, state, zone FROM stations ORDER BY station_name ASC;";
    if (mysql_query(conn, sql.c_str()) == 0) {
        MYSQL_RES* res = mysql_store_result(conn);
        if (res) {
            MYSQL_ROW row;
            while ((row = mysql_fetch_row(res))) {
                Station s;
                s.code = row[0] ? row[0] : "";
                s.name = row[1] ? row[1] : "";
                s.city = row[2] ? row[2] : "";
                s.state = row[3] ? row[3] : "";
                s.zone = row[4] ? row[4] : "";
                list.push_back(s);
            }
            mysql_free_result(res);
        }
    }
    return list;
}

std::vector<nlohmann::json> DatabaseManager::search_trains(const std::string& source, const std::string& dest, const std::string& travel_date) {
    std::vector<nlohmann::json> results;
    auto conn_wrapper = pool_.acquire();
    if (!conn_wrapper) return results;
    MYSQL* conn = conn_wrapper->get();

    std::string esc_src = escape_string(conn, source);
    std::string esc_dst = escape_string(conn, dest);
    std::string esc_date = escape_string(conn, travel_date);

    std::ostringstream ss;
    ss << "SELECT t.train_number, t.train_name, t.train_type, t.source_station, t.dest_station, "
       << "t.departure_time, t.arrival_time, t.distance_km, "
       << "s1.station_name AS src_name, s2.station_name AS dst_name "
       << "FROM trains t "
       << "JOIN stations s1 ON t.source_station = s1.station_code "
       << "JOIN stations s2 ON t.dest_station = s2.station_code "
       << "WHERE 1=1 ";
    if (!source.empty()) ss << "AND t.source_station = '" << esc_src << "' ";
    if (!dest.empty()) ss << "AND t.dest_station = '" << esc_dst << "' ";
    ss << "ORDER BY t.train_number ASC;";

    if (mysql_query(conn, ss.str().c_str()) == 0) {
        MYSQL_RES* res = mysql_store_result(conn);
        if (res) {
            MYSQL_ROW row;
            while ((row = mysql_fetch_row(res))) {
                nlohmann::json tr;
                std::string train_no = row[0] ? row[0] : "";
                tr["train_number"] = train_no;
                tr["train_name"] = row[1] ? row[1] : "";
                tr["train_type"] = row[2] ? row[2] : "";
                tr["source_code"] = row[3] ? row[3] : "";
                tr["dest_code"] = row[4] ? row[4] : "";
                tr["departure"] = row[5] ? row[5] : "";
                tr["arrival"] = row[6] ? row[6] : "";
                tr["distance_km"] = row[7] ? std::stoi(row[7]) : 0;
                tr["source_name"] = row[8] ? row[8] : "";
                tr["dest_name"] = row[9] ? row[9] : "";

                // Fetch coach classes and current seat availability for this train & date
                std::ostringstream avail_ss;
                avail_ss << "SELECT i.coach_class, i.available_seats, i.current_wl_count, MAX(tc.base_fare) AS base_fare "
                         << "FROM seat_inventory i "
                         << "JOIN train_coaches tc ON i.train_number = tc.train_number AND i.coach_class = tc.coach_class "
                         << "WHERE i.train_number = '" << escape_string(conn, train_no) << "' "
                         << "AND i.travel_date = '" << esc_date << "' "
                         << "GROUP BY i.coach_class, i.available_seats, i.current_wl_count;";

                nlohmann::json classes = nlohmann::json::array();
                if (mysql_query(conn, avail_ss.str().c_str()) == 0) {
                    MYSQL_RES* c_res = mysql_store_result(conn);
                    if (c_res) {
                        MYSQL_ROW c_row;
                        while ((c_row = mysql_fetch_row(c_res))) {
                            nlohmann::json c_obj;
                            c_obj["coach_class"] = c_row[0] ? c_row[0] : "";
                            c_obj["available_seats"] = c_row[1] ? std::stoi(c_row[1]) : 0;
                            c_obj["waiting_list_count"] = c_row[2] ? std::stoi(c_row[2]) : 0;
                            c_obj["base_fare"] = c_row[3] ? std::stod(c_row[3]) : 0.0;
                            classes.push_back(c_obj);
                        }
                        mysql_free_result(c_res);
                    }
                }
                tr["classes"] = classes;
                results.push_back(tr);
            }
            mysql_free_result(res);
        }
    }
    return results;
}

nlohmann::json DatabaseManager::get_train_availability(const std::string& train_number, const std::string& travel_date) {
    nlohmann::json res = nlohmann::json::array();
    auto conn_wrapper = pool_.acquire();
    if (!conn_wrapper) return res;
    MYSQL* conn = conn_wrapper->get();

    std::ostringstream ss;
    ss << "SELECT i.coach_class, i.total_seats, i.available_seats, i.current_wl_count, MAX(tc.base_fare) AS base_fare "
       << "FROM seat_inventory i "
       << "JOIN train_coaches tc ON i.train_number = tc.train_number AND i.coach_class = tc.coach_class "
       << "WHERE i.train_number = '" << escape_string(conn, train_number) << "' "
       << "AND i.travel_date = '" << escape_string(conn, travel_date) << "' "
       << "GROUP BY i.coach_class, i.total_seats, i.available_seats, i.current_wl_count;";

    if (mysql_query(conn, ss.str().c_str()) == 0) {
        MYSQL_RES* r = mysql_store_result(conn);
        if (r) {
            MYSQL_ROW row;
            while ((row = mysql_fetch_row(r))) {
                nlohmann::json item;
                item["coach_class"] = row[0] ? row[0] : "";
                item["total_seats"] = row[1] ? std::stoi(row[1]) : 0;
                item["available_seats"] = row[2] ? std::stoi(row[2]) : 0;
                item["waiting_list_count"] = row[3] ? std::stoi(row[3]) : 0;
                item["base_fare"] = row[4] ? std::stod(row[4]) : 0.0;
                res.push_back(item);
            }
            mysql_free_result(r);
        }
    }
    return res;
}

// ------------------------------------------------------------------------------
// ACID Booking Transaction with Row-Level Locking (Pessimistic)
// ------------------------------------------------------------------------------
BookingResult DatabaseManager::execute_booking(BookingRequest& req, int worker_thread_id) {
    BookingResult result;
    result.worker_thread_id = worker_thread_id;
    auto start_time = std::chrono::high_resolution_clock::now();

    auto conn_wrapper = pool_.acquire();
    if (!conn_wrapper) {
        result.success = false;
        result.message = "Failed to acquire database connection from pool";
        return result;
    }
    MYSQL* conn = conn_wrapper->get();

    std::string esc_train = escape_string(conn, req.train_number);
    std::string esc_date = escape_string(conn, req.travel_date);
    std::string esc_class = escape_string(conn, req.coach_class);
    std::string esc_name = escape_string(conn, req.passenger.name);
    std::string esc_gender = escape_string(conn, req.passenger.gender);
    std::string esc_phone = escape_string(conn, req.passenger.phone);
    std::string esc_email = escape_string(conn, req.passenger.email);
    std::string esc_quota = quota_to_string(req.quota);

    // 1. Insert Passenger
    std::ostringstream pass_ss;
    pass_ss << "INSERT INTO passengers (full_name, age, gender, phone, email) VALUES ('"
            << esc_name << "', " << req.passenger.age << ", '" << esc_gender << "', '"
            << esc_phone << "', '" << esc_email << "');";

    if (mysql_query(conn, pass_ss.str().c_str()) != 0) {
        result.success = false;
        result.message = "Failed to register passenger: " + std::string(mysql_error(conn));
        return result;
    }
    unsigned long long passenger_id = mysql_insert_id(conn);

    // 2. Fetch base fare for the class
    double fare = 1500.0;
    std::ostringstream fare_ss;
    fare_ss << "SELECT base_fare FROM train_coaches WHERE train_number = '" << esc_train
            << "' AND coach_class = '" << esc_class << "' LIMIT 1;";
    if (mysql_query(conn, fare_ss.str().c_str()) == 0) {
        MYSQL_RES* fres = mysql_store_result(conn);
        if (fres) {
            MYSQL_ROW frow = mysql_fetch_row(fres);
            if (frow && frow[0]) fare = std::stod(frow[0]);
            mysql_free_result(fres);
        }
    }

    // Apply Tatkal markup or Senior citizen concession
    if (req.quota == QuotaType::TATKAL) {
        fare *= 1.30; // 30% Tatkal premium
    } else if (req.quota == QuotaType::SENIOR_CITIZEN) {
        fare *= 0.60; // 40% Senior concession
    }
    result.fare = fare;

    // 3. START DATABASE TRANSACTION
    mysql_query(conn, "START TRANSACTION;");

    // 4. Row-Level Pessimistic Lock on Seat Inventory
    std::ostringstream inv_ss;
    inv_ss << "SELECT inventory_id, available_seats, current_wl_count, total_wl_seats "
           << "FROM seat_inventory "
           << "WHERE train_number = '" << esc_train << "' "
           << "AND travel_date = '" << esc_date << "' "
           << "AND coach_class = '" << esc_class << "' "
           << "FOR UPDATE;"; // PESSIMISTIC LOCK

    if (mysql_query(conn, inv_ss.str().c_str()) != 0) {
        mysql_query(conn, "ROLLBACK;");
        SystemTelemetry::instance().increment_rollbacks();
        result.success = false;
        result.message = "Transaction error on inventory lock: " + std::string(mysql_error(conn));
        return result;
    }

    MYSQL_RES* inv_res = mysql_store_result(conn);
    if (!inv_res) {
        mysql_query(conn, "ROLLBACK;");
        SystemTelemetry::instance().increment_rollbacks();
        result.success = false;
        result.message = "Inventory row not found for specified train/date.";
        return result;
    }

    MYSQL_ROW inv_row = mysql_fetch_row(inv_res);
    if (!inv_row) {
        mysql_free_result(inv_res);
        // Automatically initialize inventory for this travel date and class if not yet created
        std::ostringstream ins_inv;
        ins_inv << "INSERT INTO seat_inventory (train_number, travel_date, coach_class, total_seats, available_seats, total_wl_seats, current_wl_count) "
                << "SELECT '" << esc_train << "', '" << esc_date << "', '" << esc_class << "', "
                << "COALESCE(SUM(capacity), 72), COALESCE(SUM(capacity), 72), 30, 0 "
                << "FROM train_coaches WHERE train_number = '" << esc_train << "' AND coach_class = '" << esc_class << "' "
                << "ON DUPLICATE KEY UPDATE total_seats = total_seats;";
        mysql_query(conn, ins_inv.str().c_str());

        // Re-query with lock
        if (mysql_query(conn, inv_ss.str().c_str()) != 0) {
            mysql_query(conn, "ROLLBACK;");
            SystemTelemetry::instance().increment_rollbacks();
            result.success = false;
            result.message = "Failed to lock initialized inventory.";
            return result;
        }

        inv_res = mysql_store_result(conn);
        inv_row = inv_res ? mysql_fetch_row(inv_res) : nullptr;
        if (!inv_row) {
            if (inv_res) mysql_free_result(inv_res);
            mysql_query(conn, "ROLLBACK;");
            SystemTelemetry::instance().increment_rollbacks();
            result.success = false;
            result.message = "Class not configured for this train.";
            return result;
        }
    }

    int inventory_id = std::stoi(inv_row[0]);
    int available_seats = std::stoi(inv_row[1]);
    int current_wl = std::stoi(inv_row[2]);
    int total_wl = std::stoi(inv_row[3]);
    mysql_free_result(inv_res);

    std::string new_pnr = generate_pnr();
    result.pnr = new_pnr;

    if (available_seats > 0) {
        // CASE A: CONFIRMED SEAT AVAILABLE
        // Lock and find physical seat
        std::ostringstream seat_ss;
        seat_ss << "SELECT seat_id, coach_name, seat_number, berth_type "
                << "FROM physical_seats "
                << "WHERE train_number = '" << esc_train << "' "
                << "AND travel_date = '" << esc_date << "' "
                << "AND coach_class = '" << esc_class << "' "
                << "AND is_booked = FALSE "
                << "LIMIT 1 FOR UPDATE;";

        std::string coach_name = (esc_class == "EC" ? "E1" : (esc_class == "3A" ? "B1" : (esc_class == "2A" ? "A1" : (esc_class == "1A" ? "H1" : "C1"))));
        int seat_num = available_seats;
        std::string berth = (seat_num % 6 == 1) ? "LOWER" : ((seat_num % 6 == 2) ? "MIDDLE" : ((seat_num % 6 == 3) ? "UPPER" : ((seat_num % 6 == 4) ? "SIDE LOWER" : ((seat_num % 6 == 5) ? "SIDE UPPER" : "WINDOW"))));
        int seat_id = 0;

        if (mysql_query(conn, seat_ss.str().c_str()) == 0) {
            MYSQL_RES* seat_res = mysql_store_result(conn);
            MYSQL_ROW seat_row = seat_res ? mysql_fetch_row(seat_res) : nullptr;
            if (seat_row) {
                seat_id = std::stoi(seat_row[0]);
                coach_name = seat_row[1] ? seat_row[1] : coach_name;
                seat_num = seat_row[2] ? std::stoi(seat_row[2]) : seat_num;
                berth = seat_row[3] ? seat_row[3] : berth;

                // Mark physical seat booked
                std::ostringstream upd_seat;
                upd_seat << "UPDATE physical_seats SET is_booked = TRUE, current_pnr = '" << new_pnr
                         << "' WHERE seat_id = " << seat_id << ";";
                mysql_query(conn, upd_seat.str().c_str());
            }
            if (seat_res) mysql_free_result(seat_res);
        }

        // Deduct available seat
        std::ostringstream upd_inv;
        upd_inv << "UPDATE seat_inventory SET available_seats = available_seats - 1 WHERE inventory_id = " << inventory_id << ";";
        mysql_query(conn, upd_inv.str().c_str());

        // Insert booking record
        std::ostringstream book_ss;
        book_ss << "INSERT INTO bookings (pnr, train_number, passenger_id, travel_date, coach_class, "
                << "coach_name, seat_number, berth_type, booking_status, quota, priority_level, fare_paid) VALUES ('"
                << new_pnr << "', '" << esc_train << "', " << passenger_id << ", '" << esc_date << "', '"
                << esc_class << "', '" << coach_name << "', " << seat_num << ", '" << berth << "', "
                << "'CONFIRMED', '" << esc_quota << "', " << req.priority_level << ", " << fare << ");";

        mysql_query(conn, book_ss.str().c_str());

        // COMMIT TRANSACTION
        mysql_query(conn, "COMMIT;");
        SystemTelemetry::instance().increment_commits();
        SystemTelemetry::instance().increment_confirmed();

        result.success = true;
        result.status = BookingStatus::CONFIRMED;
        result.coach_name = coach_name;
        result.seat_number = seat_num;
        result.berth_type = berth;
        result.message = "Booking confirmed successfully!";
    } else if (current_wl < total_wl) {
        // CASE B: NO CONFIRMED SEATS, BUT WAITING LIST HAS SPACE
        int new_wl_pos = current_wl + 1;

        std::ostringstream upd_wl;
        upd_wl << "UPDATE seat_inventory SET current_wl_count = current_wl_count + 1 WHERE inventory_id = " << inventory_id << ";";
        mysql_query(conn, upd_wl.str().c_str());

        std::ostringstream book_wl;
        book_wl << "INSERT INTO bookings (pnr, train_number, passenger_id, travel_date, coach_class, "
                << "booking_status, wl_position, quota, priority_level, fare_paid) VALUES ('"
                << new_pnr << "', '" << esc_train << "', " << passenger_id << ", '" << esc_date << "', '"
                << esc_class << "', 'WAITING', " << new_wl_pos << ", '" << esc_quota << "', "
                << req.priority_level << ", " << fare << ");";

        mysql_query(conn, book_wl.str().c_str());

        // COMMIT TRANSACTION
        mysql_query(conn, "COMMIT;");
        SystemTelemetry::instance().increment_commits();
        SystemTelemetry::instance().increment_waiting();

        result.success = true;
        result.status = BookingStatus::WAITING;
        result.wl_position = new_wl_pos;
        result.message = "Seats full. Ticket issued on Waiting List (WL " + std::to_string(new_wl_pos) + ").";
    } else {
        // CASE C: REGRET (NO SEATS, WAITING LIST EXHAUSTED)
        mysql_query(conn, "ROLLBACK;");
        SystemTelemetry::instance().increment_rollbacks();

        result.success = false;
        result.status = BookingStatus::REJECTED;
        result.message = "Booking rejected: Train capacity and Waiting List exhausted (REGRET).";
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();

    // Log DBMS transaction audit
    log_transaction(worker_thread_id, 
                    result.status == BookingStatus::CONFIRMED ? "BOOKING_CONFIRMED" : (result.status == BookingStatus::WAITING ? "BOOKING_WAITING" : "BOOKING_REJECTED"),
                    result.pnr,
                    "Train: " + req.train_number + ", Class: " + req.coach_class + ", Quota: " + esc_quota + ", Priority: " + std::to_string(req.priority_level),
                    result.success ? "COMMITTED" : "ROLLEDBACK",
                    result.execution_time_ms);

    return result;
}

// ------------------------------------------------------------------------------
// Cancellation & Automatic Waiting-List Promotion Transaction
// ------------------------------------------------------------------------------
CancellationResult DatabaseManager::execute_cancellation(const std::string& pnr, int worker_thread_id) {
    CancellationResult result;
    result.pnr = pnr;
    auto start_time = std::chrono::high_resolution_clock::now();

    auto conn_wrapper = pool_.acquire();
    if (!conn_wrapper) {
        result.success = false;
        result.message = "Database connection unavailable.";
        return result;
    }
    MYSQL* conn = conn_wrapper->get();
    std::string esc_pnr = escape_string(conn, pnr);

    // 1. START TRANSACTION
    mysql_query(conn, "START TRANSACTION;");

    // 2. Lock the target booking record
    std::ostringstream find_ss;
    find_ss << "SELECT booking_id, train_number, travel_date, coach_class, coach_name, "
            << "seat_number, berth_type, booking_status, fare_paid "
            << "FROM bookings WHERE pnr = '" << esc_pnr << "' FOR UPDATE;";

    if (mysql_query(conn, find_ss.str().c_str()) != 0) {
        mysql_query(conn, "ROLLBACK;");
        SystemTelemetry::instance().increment_rollbacks();
        result.success = false;
        result.message = "Error querying booking: " + std::string(mysql_error(conn));
        return result;
    }

    MYSQL_RES* b_res = mysql_store_result(conn);
    MYSQL_ROW b_row = b_res ? mysql_fetch_row(b_res) : nullptr;

    if (!b_row) {
        if (b_res) mysql_free_result(b_res);
        mysql_query(conn, "ROLLBACK;");
        SystemTelemetry::instance().increment_rollbacks();
        result.success = false;
        result.message = "No booking found with PNR " + pnr;
        return result;
    }

    int booking_id = std::stoi(b_row[0]);
    std::string train_no = b_row[1] ? b_row[1] : "";
    std::string travel_date = b_row[2] ? b_row[2] : "";
    std::string coach_class = b_row[3] ? b_row[3] : "";
    std::string coach_name = b_row[4] ? b_row[4] : "";
    int seat_num = b_row[5] ? std::stoi(b_row[5]) : 0;
    std::string berth = b_row[6] ? b_row[6] : "";
    std::string status = b_row[7] ? b_row[7] : "";
    double fare_paid = b_row[8] ? std::stod(b_row[8]) : 0.0;
    mysql_free_result(b_res);

    if (status == "CANCELLED") {
        mysql_query(conn, "ROLLBACK;");
        SystemTelemetry::instance().increment_rollbacks();
        result.success = false;
        result.message = "Ticket is already cancelled.";
        return result;
    }

    // Mark current booking CANCELLED
    std::ostringstream cancel_ss;
    cancel_ss << "UPDATE bookings SET booking_status = 'CANCELLED' WHERE booking_id = " << booking_id << ";";
    mysql_query(conn, cancel_ss.str().c_str());

    result.refund_amount = fare_paid * 0.85; // 85% refund after IRCTC cancellation charges

    if (status == "CONFIRMED") {
        // Search for highest priority Waiting List passenger to promote!
        std::ostringstream wl_ss;
        wl_ss << "SELECT booking_id, pnr FROM bookings "
              << "WHERE train_number = '" << escape_string(conn, train_no) << "' "
              << "AND travel_date = '" << escape_string(conn, travel_date) << "' "
              << "AND coach_class = '" << escape_string(conn, coach_class) << "' "
              << "AND booking_status = 'WAITING' "
              << "ORDER BY priority_level ASC, wl_position ASC, booking_id ASC "
              << "LIMIT 1 FOR UPDATE;";

        mysql_query(conn, wl_ss.str().c_str());
        MYSQL_RES* wl_res = mysql_store_result(conn);
        MYSQL_ROW wl_row = wl_res ? mysql_fetch_row(wl_res) : nullptr;

        if (wl_row) {
            // PROMOTE WAITING LIST PASSENGER!
            int top_wl_id = std::stoi(wl_row[0]);
            std::string top_wl_pnr = wl_row[1] ? wl_row[1] : "";
            mysql_free_result(wl_res);

            // Update promoted passenger to CONFIRMED and reallocate the freed seat
            std::ostringstream promo_ss;
            promo_ss << "UPDATE bookings SET booking_status = 'CONFIRMED', "
                     << "coach_name = '" << escape_string(conn, coach_name) << "', "
                     << "seat_number = " << seat_num << ", "
                     << "berth_type = '" << escape_string(conn, berth) << "', "
                     << "wl_position = NULL "
                     << "WHERE booking_id = " << top_wl_id << ";";
            mysql_query(conn, promo_ss.str().c_str());

            // Update physical seat to hold the promoted passenger's PNR
            std::ostringstream upd_seat;
            upd_seat << "UPDATE physical_seats SET current_pnr = '" << escape_string(conn, top_wl_pnr) << "' "
                     << "WHERE train_number = '" << escape_string(conn, train_no) << "' "
                     << "AND travel_date = '" << escape_string(conn, travel_date) << "' "
                     << "AND coach_name = '" << escape_string(conn, coach_name) << "' "
                     << "AND seat_number = " << seat_num << ";";
            mysql_query(conn, upd_seat.str().c_str());

            // Decrement waiting list count
            std::ostringstream upd_inv;
            upd_inv << "UPDATE seat_inventory SET current_wl_count = GREATEST(0, current_wl_count - 1) "
                    << "WHERE train_number = '" << escape_string(conn, train_no) << "' "
                    << "AND travel_date = '" << escape_string(conn, travel_date) << "' "
                    << "AND coach_class = '" << escape_string(conn, coach_class) << "';";
            mysql_query(conn, upd_inv.str().c_str());

            result.promoted_waiting_passenger = true;
            result.promoted_pnr = top_wl_pnr;
            SystemTelemetry::instance().increment_promotions();
        } else {
            if (wl_res) mysql_free_result(wl_res);

            // No WL passenger: Release physical seat and increment available seats
            std::ostringstream free_seat;
            free_seat << "UPDATE physical_seats SET is_booked = FALSE, current_pnr = NULL "
                      << "WHERE train_number = '" << escape_string(conn, train_no) << "' "
                      << "AND travel_date = '" << escape_string(conn, travel_date) << "' "
                      << "AND coach_name = '" << escape_string(conn, coach_name) << "' "
                      << "AND seat_number = " << seat_num << ";";
            mysql_query(conn, free_seat.str().c_str());

            std::ostringstream inc_inv;
            inc_inv << "UPDATE seat_inventory SET available_seats = available_seats + 1 "
                    << "WHERE train_number = '" << escape_string(conn, train_no) << "' "
                    << "AND travel_date = '" << escape_string(conn, travel_date) << "' "
                    << "AND coach_class = '" << escape_string(conn, coach_class) << "';";
            mysql_query(conn, inc_inv.str().c_str());
        }
    } else if (status == "WAITING") {
        // Simply reduce waiting list count
        std::ostringstream dec_wl;
        dec_wl << "UPDATE seat_inventory SET current_wl_count = GREATEST(0, current_wl_count - 1) "
               << "WHERE train_number = '" << escape_string(conn, train_no) << "' "
               << "AND travel_date = '" << escape_string(conn, travel_date) << "' "
               << "AND coach_class = '" << escape_string(conn, coach_class) << "';";
        mysql_query(conn, dec_wl.str().c_str());
    }

    // COMMIT TRANSACTION
    mysql_query(conn, "COMMIT;");
    SystemTelemetry::instance().increment_commits();
    SystemTelemetry::instance().increment_cancellations();

    auto end_time = std::chrono::high_resolution_clock::now();
    result.execution_time_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
    result.success = true;
    result.message = result.promoted_waiting_passenger 
        ? "Ticket cancelled. Waiting-list passenger " + result.promoted_pnr + " was automatically promoted to CONFIRMED!"
        : "Ticket cancelled successfully. Seat restored to general availability.";

    log_transaction(worker_thread_id, "CANCELLATION", pnr,
                    result.message + " Refund: Rs. " + std::to_string(result.refund_amount),
                    "COMMITTED", result.execution_time_ms);

    return result;
}

// ------------------------------------------------------------------------------
// PNR Query
// ------------------------------------------------------------------------------
nlohmann::json DatabaseManager::get_booking_by_pnr(const std::string& pnr) {
    nlohmann::json info;
    auto conn_wrapper = pool_.acquire();
    if (!conn_wrapper) return info;
    MYSQL* conn = conn_wrapper->get();

    std::ostringstream ss;
    ss << "SELECT b.pnr, b.train_number, t.train_name, t.source_station, t.dest_station, "
       << "b.travel_date, b.coach_class, b.coach_name, b.seat_number, b.berth_type, "
       << "b.booking_status, b.wl_position, b.quota, b.fare_paid, b.created_at, "
       << "p.full_name, p.age, p.gender, p.phone "
       << "FROM bookings b "
       << "JOIN trains t ON b.train_number = t.train_number "
       << "JOIN passengers p ON b.passenger_id = p.passenger_id "
       << "WHERE b.pnr = '" << escape_string(conn, pnr) << "' LIMIT 1;";

    if (mysql_query(conn, ss.str().c_str()) == 0) {
        MYSQL_RES* res = mysql_store_result(conn);
        if (res) {
            MYSQL_ROW row = mysql_fetch_row(res);
            if (row) {
                info["found"] = true;
                info["pnr"] = row[0] ? row[0] : "";
                info["train_number"] = row[1] ? row[1] : "";
                info["train_name"] = row[2] ? row[2] : "";
                info["source"] = row[3] ? row[3] : "";
                info["dest"] = row[4] ? row[4] : "";
                info["travel_date"] = row[5] ? row[5] : "";
                info["coach_class"] = row[6] ? row[6] : "";
                info["coach_name"] = row[7] ? row[7] : "NA";
                info["seat_number"] = row[8] ? std::stoi(row[8]) : 0;
                info["berth_type"] = row[9] ? row[9] : "NA";
                info["booking_status"] = row[10] ? row[10] : "";
                info["wl_position"] = row[11] ? std::stoi(row[11]) : 0;
                info["quota"] = row[12] ? row[12] : "";
                info["fare_paid"] = row[13] ? std::stod(row[13]) : 0.0;
                info["created_at"] = row[14] ? row[14] : "";
                info["passenger_name"] = row[15] ? row[15] : "";
                info["age"] = row[16] ? std::stoi(row[16]) : 0;
                info["gender"] = row[17] ? row[17] : "";
                info["phone"] = row[18] ? row[18] : "";
            } else {
                info["found"] = false;
                info["message"] = "PNR not found.";
            }
            mysql_free_result(res);
        }
    }
    return info;
}

// ------------------------------------------------------------------------------
// Fetch Recent Database Transactions Log for Live Dashboard
// ------------------------------------------------------------------------------
std::vector<TransactionRecord> DatabaseManager::get_recent_transaction_logs(int limit) {
    std::vector<TransactionRecord> list;
    auto conn_wrapper = pool_.acquire();
    if (!conn_wrapper) return list;
    MYSQL* conn = conn_wrapper->get();

    std::ostringstream ss;
    ss << "SELECT log_id, thread_id, operation, pnr, details, status, execution_time_ms, created_at "
       << "FROM db_transactions_log ORDER BY log_id DESC LIMIT " << limit << ";";

    if (mysql_query(conn, ss.str().c_str()) == 0) {
        MYSQL_RES* res = mysql_store_result(conn);
        if (res) {
            MYSQL_ROW row;
            while ((row = mysql_fetch_row(res))) {
                TransactionRecord r;
                r.log_id = row[0] ? std::stoi(row[0]) : 0;
                r.thread_id = row[1] ? std::stoi(row[1]) : 0;
                r.operation = row[2] ? row[2] : "";
                r.pnr = row[3] ? row[3] : "-";
                r.details = row[4] ? row[4] : "";
                r.status = row[5] ? row[5] : "";
                r.execution_time_ms = row[6] ? std::stod(row[6]) : 0.0;
                r.created_at = row[7] ? row[7] : "";
                list.push_back(r);
            }
            mysql_free_result(res);
        }
    }
    return list;
}

} // namespace railway
