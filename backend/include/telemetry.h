#pragma once
#include <string>
#include <vector>
#include <atomic>
#include <mutex>
#include <chrono>

namespace smartrail {

struct TelemetrySnapshot {
    long long total_requests = 0;
    long long completed_requests = 0;
    long long failed_requests = 0;
    long long pending_requests = 0;
    int active_workers = 0;
    int queue_depth = 0;
    double avg_processing_time_ms = 0.0;
    double avg_queue_wait_ms = 0.0;
    long long lock_contentions = 0;
};

class TelemetryTracker {
public:
    static TelemetryTracker& instance();

    void record_request_enqueued();
    void record_request_completed(double proc_time_ms, double wait_time_ms);
    void record_request_failed();
    void record_lock_contention();
    void set_active_workers(int count);
    void set_queue_depth(int depth);

    TelemetrySnapshot get_snapshot();

private:
    TelemetryTracker() = default;

    std::atomic<long long> total_requests_{0};
    std::atomic<long long> completed_requests_{0};
    std::atomic<long long> failed_requests_{0};
    std::atomic<long long> lock_contentions_{0};
    std::atomic<int> active_workers_{0};
    std::atomic<int> current_queue_depth_{0};

    std::mutex metrics_mutex_;
    std::vector<double> recent_proc_times_;
    std::vector<double> recent_wait_times_;
};

} // namespace smartrail
