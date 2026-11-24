#pragma once
#include <string>
#include <memory>
#include <mutex>

namespace smartrail {

class DBConnection {
public:
    static DBConnection& instance();

    bool connect(const std::string& host, int port, const std::string& user,
                 const std::string& password, const std::string& dbname);
    void disconnect();
    bool is_connected() const { return connected_; }

    // Query execution abstraction with row-level locking support
    bool execute_transaction(const std::string& sql);

private:
    DBConnection() = default;
    bool connected_ = false;
    std::mutex db_mutex_;
};

} // namespace smartrail
