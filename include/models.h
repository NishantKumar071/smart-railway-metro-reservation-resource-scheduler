#pragma once
#include <string>
#include <vector>
#include <chrono>
#include <memory>
#include <future>

namespace railway {

// ------------------------------------------------------------------------------
// Booking Quota & Priority Levels (OS Scheduling)
// ------------------------------------------------------------------------------
enum class QuotaType {
    EMERGENCY = 1,       // Priority 1: VIP / Defense / Critical Medical (Highest)
    SENIOR_CITIZEN = 2,  // Priority 2: Age >= 60 concession & lower-berth priority
    TATKAL = 3,          // Priority 3: Last-minute premium reservation
    NORMAL = 4           // Priority 4: General public (Standard FCFS)
};

inline std::string quota_to_string(QuotaType q) {
    switch (q) {
        case QuotaType::EMERGENCY: return "EMERGENCY";
        case QuotaType::SENIOR_CITIZEN: return "SENIOR_CITIZEN";
        case QuotaType::TATKAL: return "TATKAL";
        case QuotaType::NORMAL: return "NORMAL";
        default: return "NORMAL";
    }
}

inline QuotaType string_to_quota(const std::string& str) {
    if (str == "EMERGENCY") return QuotaType::EMERGENCY;
    if (str == "SENIOR_CITIZEN" || str == "SENIOR") return QuotaType::SENIOR_CITIZEN;
    if (str == "TATKAL") return QuotaType::TATKAL;
    return QuotaType::NORMAL;
}

// ------------------------------------------------------------------------------
// Booking Status
// ------------------------------------------------------------------------------
enum class BookingStatus {
    CONFIRMED,
    WAITING,
    CANCELLED,
    REJECTED
};

inline std::string status_to_string(BookingStatus s) {
    switch (s) {
        case BookingStatus::CONFIRMED: return "CONFIRMED";
        case BookingStatus::WAITING: return "WAITING";
        case BookingStatus::CANCELLED: return "CANCELLED";
        case BookingStatus::REJECTED: return "REJECTED";
        default: return "UNKNOWN";
    }
}

// ------------------------------------------------------------------------------
// Domain Data Models
// ------------------------------------------------------------------------------
struct Station {
    std::string code;
    std::string name;
    std::string city;
    std::string state;
    std::string zone;
};

struct Train {
    std::string number;
    std::string name;
    std::string type;
    std::string source;
    std::string dest;
    std::string departure;
    std::string arrival;
    int distance_km = 0;
};

struct SeatAvailability {
    std::string train_number;
    std::string travel_date;
    std::string coach_class;
    int total_seats = 0;
    int available_seats = 0;
    int waiting_list_count = 0;
    double base_fare = 0.0;
};

struct Passenger {
    int passenger_id = 0;
    std::string name;
    int age = 0;
    std::string gender;
    std::string phone;
    std::string email;
};

struct BookingResult {
    bool success = false;
    std::string pnr;
    BookingStatus status = BookingStatus::REJECTED;
    std::string coach_name;
    int seat_number = 0;
    std::string berth_type;
    int wl_position = 0;
    double fare = 0.0;
    std::string message;
    double execution_time_ms = 0.0;
    int worker_thread_id = 0;
};

struct CancellationResult {
    bool success = false;
    std::string pnr;
    std::string message;
    bool promoted_waiting_passenger = false;
    std::string promoted_pnr;
    double refund_amount = 0.0;
    double execution_time_ms = 0.0;
};

// ------------------------------------------------------------------------------
// OS Scheduler Request (Task)
// ------------------------------------------------------------------------------
struct BookingRequest {
    int request_id = 0;
    std::string train_number;
    std::string travel_date;
    std::string coach_class;
    Passenger passenger;
    QuotaType quota = QuotaType::NORMAL;
    int priority_level = 4; // 1 (Highest) to 4 (Lowest)
    std::chrono::steady_clock::time_point timestamp;
    
    // Shared promise to communicate result back to calling thread/HTTP client
    std::shared_ptr<std::promise<BookingResult>> result_promise;
};

// Custom comparator for OS Priority Queue
struct BookingPriorityComparator {
    bool operator()(const BookingRequest& a, const BookingRequest& b) const {
        // Lower numerical priority_level means HIGHER scheduling priority
        if (a.priority_level != b.priority_level) {
            return a.priority_level > b.priority_level;
        }
        // FCFS for identical priority
        return a.timestamp > b.timestamp;
    }
};

struct TransactionRecord {
    int log_id = 0;
    int thread_id = 0;
    std::string operation;
    std::string pnr;
    std::string details;
    std::string status;
    double execution_time_ms = 0.0;
    std::string created_at;
};

} // namespace railway
