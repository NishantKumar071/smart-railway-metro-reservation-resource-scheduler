#pragma once
#include <string>

namespace smartrail {

struct Config {
    std::string db_host = "localhost";
    int db_port = 3306;
    std::string db_name = "smartrail_db";
    std::string db_user = "root";
    std::string db_pass = "";
    int server_port = 8080;
    int worker_threads = 6;
    int max_queue_size = 100;
    std::string ai_service_url = "http://localhost:8000";

    static Config from_env();
};

} // namespace smartrail
