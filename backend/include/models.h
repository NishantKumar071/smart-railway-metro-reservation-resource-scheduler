#pragma once
#include <string>
#include <vector>
#include <chrono>

namespace smartrail {

enum class PriorityLevel {
    EMERGENCY = 1,      // Highest
    SENIOR_CITIZEN = 2,
    TATKAL = 3,
    NORMAL = 4          // Lowest
};

inline std::string priority_to_string(PriorityLevel p) {
    switch(p) {
        case PriorityLevel::EMERGENCY: return "EMERGENCY";
        case PriorityLevel::SENIOR_CITIZEN: return "SENIOR_CITIZEN";
        case PriorityLevel::TATKAL: return "TATKAL";
        case PriorityLevel::NORMAL: return "NORMAL";
        default: return "NORMAL";
    }
}

inline PriorityLevel quota_to_priority(const std::string& quota) {
    if (quota == "EMERGENCY") return PriorityLevel::EMERGENCY;
    if (quota == "SENIOR_CITIZEN") return PriorityLevel::SENIOR_CITIZEN;
    if (quota == "TATKAL") return PriorityLevel::TATKAL;
    return PriorityLevel::NORMAL;
}

struct Passenger {
    std::string full_name;
    int age = 0;
    std::string gender = "MALE";
    std::string id_type = "AADHAAR";
    std::string phone;
    std::string seat_number;
    std::string berth_allotted;
    int waitlist_number = 0;
};

struct BookingRequestData {
    std::string request_id;
    int user_id = 1;
    int train_id = 0;
    int coach_id = 0;
    std::string coach_number;
    std::string journey_date;
    std::string source_station;
    std::string dest_station;
    std::string travel_class;
    std::string quota = "GENERAL";
    std::string preferred_berth = "NO_PREFERENCE";
    double total_fare = 0.0;
    std::vector<Passenger> passengers;
    std::chrono::steady_clock::time_point enqueue_time;
};

struct BookingResult {
    bool success = false;
    std::string pnr;
    std::string booking_status; // CONFIRMED, WAITING, CANCELLED
    std::string coach_number;
    std::string seat_number;
    std::string berth_allotted;
    int waitlist_number = 0;
    double total_fare = 0.0;
    std::string message;
    int worker_thread_id = 0;
    long long processing_time_ms = 0;
    long long queue_wait_time_ms = 0;
};

} // namespace smartrail
