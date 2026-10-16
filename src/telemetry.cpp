#include "telemetry.h"

namespace railway {

SystemTelemetry& SystemTelemetry::instance() {
    static SystemTelemetry instance_;
    return instance_;
}

void SystemTelemetry::increment_emergency_served() {
    total_requests_++;
    emergency_count_++;
}

void SystemTelemetry::increment_senior_served() {
    total_requests_++;
    senior_count_++;
}

void SystemTelemetry::increment_tatkal_served() {
    total_requests_++;
    tatkal_count_++;
}

void SystemTelemetry::increment_normal_served() {
    total_requests_++;
    normal_count_++;
}

void SystemTelemetry::increment_contention() {
    contention_events_++;
}

void SystemTelemetry::set_active_threads(int count) {
    active_threads_ = count;
}

void SystemTelemetry::set_queue_size(int size) {
    current_queue_size_ = size;
}

void SystemTelemetry::increment_confirmed() {
    confirmed_count_++;
}

void SystemTelemetry::increment_waiting() {
    waiting_count_++;
}

void SystemTelemetry::increment_cancellations() {
    cancellations_count_++;
}

void SystemTelemetry::increment_promotions() {
    promotions_count_++;
}

void SystemTelemetry::increment_commits() {
    dbms_commits_++;
}

void SystemTelemetry::increment_rollbacks() {
    dbms_rollbacks_++;
}

nlohmann::json SystemTelemetry::to_json() {
    nlohmann::json j;
    j["os"] = {
        {"total_requests", total_requests_.load()},
        {"active_worker_threads", active_threads_.load()},
        {"current_queue_size", current_queue_size_.load()},
        {"priority_breakdown", {
            {"emergency", emergency_count_.load()},
            {"senior_citizen", senior_count_.load()},
            {"tatkal", tatkal_count_.load()},
            {"normal", normal_count_.load()}
        }},
        {"contention_events", contention_events_.load()}
    };

    j["dbms"] = {
        {"confirmed_bookings", confirmed_count_.load()},
        {"waiting_list_bookings", waiting_count_.load()},
        {"cancellations", cancellations_count_.load()},
        {"waiting_list_promotions", promotions_count_.load()},
        {"transactions_committed", dbms_commits_.load()},
        {"transactions_rolled_back", dbms_rollbacks_.load()}
    };

    return j;
}

} // namespace railway
