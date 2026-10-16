#pragma once
#include <atomic>
#include <string>
#include "json.hpp"

namespace railway {

class SystemTelemetry {
public:
    static SystemTelemetry& instance();

    // OS Metrics
    void increment_emergency_served();
    void increment_senior_served();
    void increment_tatkal_served();
    void increment_normal_served();
    void increment_contention();
    void set_active_threads(int count);
    void set_queue_size(int size);

    // DBMS Metrics
    void increment_confirmed();
    void increment_waiting();
    void increment_cancellations();
    void increment_promotions();
    void increment_commits();
    void increment_rollbacks();

    // Export real-time metrics to JSON for the dashboard
    nlohmann::json to_json();

private:
    SystemTelemetry() = default;

    std::atomic<long long> total_requests_{0};
    std::atomic<int> emergency_count_{0};
    std::atomic<int> senior_count_{0};
    std::atomic<int> tatkal_count_{0};
    std::atomic<int> normal_count_{0};
    std::atomic<int> contention_events_{0};

    std::atomic<int> active_threads_{0};
    std::atomic<int> current_queue_size_{0};

    std::atomic<int> confirmed_count_{0};
    std::atomic<int> waiting_count_{0};
    std::atomic<int> cancellations_count_{0};
    std::atomic<int> promotions_count_{0};

    std::atomic<int> dbms_commits_{0};
    std::atomic<int> dbms_rollbacks_{0};
};

} // namespace railway
