#include "telemetry.h"
#include <numeric>

namespace smartrail {

TelemetryTracker& TelemetryTracker::instance() {
    static TelemetryTracker inst;
    return inst;
}

void TelemetryTracker::record_request_enqueued() {
    total_requests_++;
}

void TelemetryTracker::record_request_completed(double proc_time_ms, double wait_time_ms) {
    completed_requests_++;
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    recent_proc_times_.push_back(proc_time_ms);
    if (recent_proc_times_.size() > 500) recent_proc_times_.erase(recent_proc_times_.begin());

    recent_wait_times_.push_back(wait_time_ms);
    if (recent_wait_times_.size() > 500) recent_wait_times_.erase(recent_wait_times_.begin());
}

void TelemetryTracker::record_request_failed() {
    failed_requests_++;
}

void TelemetryTracker::record_lock_contention() {
    lock_contentions_++;
}

void TelemetryTracker::set_active_workers(int count) {
    active_workers_ = count;
}

void TelemetryTracker::set_queue_depth(int depth) {
    current_queue_depth_ = depth;
}

TelemetrySnapshot TelemetryTracker::get_snapshot() {
    TelemetrySnapshot s;
    s.total_requests = total_requests_.load();
    s.completed_requests = completed_requests_.load();
    s.failed_requests = failed_requests_.load();
    s.pending_requests = s.total_requests - s.completed_requests - s.failed_requests;
    s.active_workers = active_workers_.load();
    s.queue_depth = current_queue_depth_.load();
    s.lock_contentions = lock_contentions_.load();

    std::lock_guard<std::mutex> lock(metrics_mutex_);
    if (!recent_proc_times_.empty()) {
        double sum = std::accumulate(recent_proc_times_.begin(), recent_proc_times_.end(), 0.0);
        s.avg_processing_time_ms = sum / recent_proc_times_.size();
    }
    if (!recent_wait_times_.empty()) {
        double sum = std::accumulate(recent_wait_times_.begin(), recent_wait_times_.end(), 0.0);
        s.avg_queue_wait_ms = sum / recent_wait_times_.size();
    }
    return s;
}

} // namespace smartrail
