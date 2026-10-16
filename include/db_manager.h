#pragma once
#include <string>
#include <vector>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <memory>
#include <mysql.h>
#include "models.h"
#include "json.hpp"

namespace railway {

struct DBConfig {
    std::string host = "localhost";
    std::string user = "root";
    std::string password = "Root@123";
    std::string database = "smart_railway_db";
    unsigned int port = 3306;
};

// RAII Wrapper for a single MySQL connection checked out from the pool
class DBConnectionPool;
class ScopedConnection {
public:
    ScopedConnection(DBConnectionPool& pool, MYSQL* conn);
    ~ScopedConnection();
    MYSQL* get() const { return conn_; }
    MYSQL* operator->() const { return conn_; }

    ScopedConnection(const ScopedConnection&) = delete;
    ScopedConnection& operator=(const ScopedConnection&) = delete;

private:
    DBConnectionPool& pool_;
    MYSQL* conn_;
};

// Thread-safe pool of MySQL connections
class DBConnectionPool {
public:
    DBConnectionPool(const DBConfig& config, size_t pool_size = 8);
    ~DBConnectionPool();

    std::unique_ptr<ScopedConnection> acquire();
    void release(MYSQL* conn);

private:
    MYSQL* create_connection();

    DBConfig config_;
    size_t pool_size_;
    std::queue<MYSQL*> pool_;
    std::mutex mutex_;
    std::condition_variable cv_;
    bool stopped_{false};
};

class DatabaseManager {
public:
    DatabaseManager(const DBConfig& config, size_t pool_size = 8);
    ~DatabaseManager() = default;

    // Station & Train Queries
    std::vector<Station> get_all_stations();
    std::vector<nlohmann::json> search_trains(const std::string& source, const std::string& dest, const std::string& travel_date);
    nlohmann::json get_train_availability(const std::string& train_number, const std::string& travel_date);

    // Core ACID Transactions
    BookingResult execute_booking(BookingRequest& req, int worker_thread_id);
    CancellationResult execute_cancellation(const std::string& pnr, int worker_thread_id);

    // Queries & Audit
    nlohmann::json get_booking_by_pnr(const std::string& pnr);
    std::vector<TransactionRecord> get_recent_transaction_logs(int limit = 30);
    void log_transaction(int thread_id, const std::string& op, const std::string& pnr, 
                         const std::string& details, const std::string& status, double duration_ms);

    DBConnectionPool& get_pool() { return pool_; }

private:
    std::string generate_pnr();
    std::string escape_string(MYSQL* conn, const std::string& str);

    DBConfig config_;
    DBConnectionPool pool_;
};

} // namespace railway
