#include "db_connection.h"
#include <iostream>

namespace smartrail {

DBConnection& DBConnection::instance() {
    static DBConnection inst;
    return inst;
}

bool DBConnection::connect(const std::string& host, int port, const std::string& user,
                           const std::string& password, const std::string& dbname) {
    std::lock_guard<std::mutex> lock(db_mutex_);
    (void)password;
    std::cout << "[DBConnection] Connecting to " << host << ":" << port
              << " user=" << user << " db=" << dbname << "...\n";
    connected_ = true;
    return true;
}

void DBConnection::disconnect() {
    std::lock_guard<std::mutex> lock(db_mutex_);
    connected_ = false;
    std::cout << "[DBConnection] Disconnected.\n";
}

bool DBConnection::execute_transaction(const std::string& sql) {
    std::lock_guard<std::mutex> lock(db_mutex_);
    (void)sql;
    return true;
}

} // namespace smartrail
