#include "scheduler.h"
#include "booking_engine.h"
#include "telemetry.h"
#include <iostream>

namespace smartrail {

PriorityScheduler::PriorityScheduler(int num_workers, int max_queue_size)
    : num_workers_(num_workers), max_queue_size_(max_queue_size) {}

PriorityScheduler::~PriorityScheduler() {
    stop();
}

void PriorityScheduler::start() {
    if (is_running_) return;
    is_running_ = true;

    for (int i = 1; i <= num_workers_; ++i) {
        workers_.emplace_back(&PriorityScheduler::worker_thread_loop, this, i);
    }
    TelemetryTracker::instance().set_active_workers(num_workers_);
    std::cout << "[PriorityScheduler] Started " << num_workers_ << " worker threads.\n";
}

void PriorityScheduler::stop() {
    if (!is_running_) return;
    is_running_ = false;

    cv_not_empty_.notify_all();
    for (auto& w : workers_) {
        if (w.joinable()) {
            w.join();
        }
    }
    workers_.clear();
    std::cout << "[PriorityScheduler] Stopped all worker threads cleanly.\n";
}

std::future<BookingResult> PriorityScheduler::submit_booking(const BookingRequestData& data) {
    auto promise = std::make_shared<std::promise<BookingResult>>();
    std::future<BookingResult> future = promise->get_future();

    PrioritizedTask task;
    task.priority = quota_to_priority(data.quota);
    task.arrival_time = std::chrono::steady_clock::now();
    task.request_id = data.request_id;
    task.data = data;
    task.data.enqueue_time = task.arrival_time;
    task.result_promise = promise;

    {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        if (static_cast<int>(task_queue_.size()) >= max_queue_size_) {
            TelemetryTracker::instance().record_lock_contention();
            cv_not_full_.wait(lock, [this]() {
                return !is_running_ || static_cast<int>(task_queue_.size()) < max_queue_size_;
            });
        }

        if (!is_running_) {
            BookingResult res;
            res.success = false;
            res.message = "Scheduler has been stopped";
            promise->set_value(res);
            return future;
        }

        task_queue_.push(std::move(task));
        TelemetryTracker::instance().record_request_enqueued();
        TelemetryTracker::instance().set_queue_depth(static_cast<int>(task_queue_.size()));
    }

    cv_not_empty_.notify_one();
    return future;
}

int PriorityScheduler::get_queue_size() {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    return static_cast<int>(task_queue_.size());
}

void PriorityScheduler::worker_thread_loop(int worker_id) {
    while (is_running_) {
        PrioritizedTask task;
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            while (task_queue_.empty() && is_running_) {
                TelemetryTracker::instance().record_lock_contention();
                cv_not_empty_.wait(lock);
            }

            if (!is_running_ && task_queue_.empty()) {
                break;
            }

            task = task_queue_.top();
            task_queue_.pop();
            TelemetryTracker::instance().set_queue_depth(static_cast<int>(task_queue_.size()));
            cv_not_full_.notify_one();
        }

        auto start_proc = std::chrono::steady_clock::now();
        double wait_ms = std::chrono::duration<double, std::milli>(start_proc - task.arrival_time).count();

        // Process actual booking through DBMS transaction logic
        BookingResult result = BookingEngine::instance().process_booking(task.data, worker_id);
        auto end_proc = std::chrono::steady_clock::now();
        double proc_ms = std::chrono::duration<double, std::milli>(end_proc - start_proc).count();

        result.worker_thread_id = worker_id;
        result.queue_wait_time_ms = static_cast<long long>(wait_ms);
        result.processing_time_ms = static_cast<long long>(proc_ms);

        if (result.success) {
            TelemetryTracker::instance().record_request_completed(proc_ms, wait_ms);
        } else {
            TelemetryTracker::instance().record_request_failed();
        }

        task.result_promise->set_value(result);
    }
}

} // namespace smartrail
