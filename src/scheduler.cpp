#include "scheduler.h"
#include "telemetry.h"
#include <iostream>

namespace railway {

ResourceScheduler::ResourceScheduler(DatabaseManager& db_mgr, size_t worker_threads)
    : db_mgr_(db_mgr), worker_count_(worker_threads) {
    for (size_t i = 1; i <= worker_count_; ++i) {
        workers_.emplace_back(&ResourceScheduler::worker_loop, this, static_cast<int>(i));
    }
    std::cout << "[ResourceScheduler] Spawned " << worker_count_ << " OS worker threads for concurrent request handling." << std::endl;
}

ResourceScheduler::~ResourceScheduler() {
    shutdown();
}

void ResourceScheduler::shutdown() {
    if (!is_running_.exchange(false)) {
        return;
    }

    cv_queue_.notify_all();
    for (auto& t : workers_) {
        if (t.joinable()) {
            t.join();
        }
    }
    std::cout << "[ResourceScheduler] All worker threads terminated cleanly." << std::endl;
}

std::mutex& ResourceScheduler::get_train_mutex(const std::string& train_number) {
    std::lock_guard<std::mutex> lock(train_map_mutex_);
    auto it = train_mutexes_.find(train_number);
    if (it == train_mutexes_.end()) {
        auto ins = train_mutexes_.emplace(train_number, std::make_unique<std::mutex>());
        return *(ins.first->second);
    }
    return *(it->second);
}

std::future<BookingResult> ResourceScheduler::enqueue_booking(BookingRequest request) {
    auto promise = std::make_shared<std::promise<BookingResult>>();
    auto future = promise->get_future();
    request.result_promise = promise;
    request.timestamp = std::chrono::steady_clock::now();

    // Map quota to numeric priority (1=EMERGENCY, 2=SENIOR_CITIZEN, 3=TATKAL, 4=NORMAL)
    request.priority_level = static_cast<int>(request.quota);

    {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        priority_queue_.push(request);
        SystemTelemetry::instance().set_queue_size(static_cast<int>(priority_queue_.size()));
    }

    // Wake up one sleeping consumer worker thread
    cv_queue_.notify_one();
    return future;
}

size_t ResourceScheduler::get_queue_size() {
    std::unique_lock<std::mutex> lock(queue_mutex_);
    return priority_queue_.size();
}

void ResourceScheduler::worker_loop(int worker_id) {
    while (is_running_) {
        BookingRequest req;

        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            cv_queue_.wait(lock, [this]() {
                return !is_running_ || !priority_queue_.empty();
            });

            if (!is_running_ && priority_queue_.empty()) {
                return;
            }

            // Dequeue highest priority request (Priority 1: Emergency -> 2: Senior -> 3: Tatkal -> 4: Normal)
            req = priority_queue_.top();
            priority_queue_.pop();
            SystemTelemetry::instance().set_queue_size(static_cast<int>(priority_queue_.size()));
        }

        // Record telemetry for priority quota scheduling
        switch (req.quota) {
            case QuotaType::EMERGENCY:
                SystemTelemetry::instance().increment_emergency_served();
                break;
            case QuotaType::SENIOR_CITIZEN:
                SystemTelemetry::instance().increment_senior_served();
                break;
            case QuotaType::TATKAL:
                SystemTelemetry::instance().increment_tatkal_served();
                break;
            case QuotaType::NORMAL:
            default:
                SystemTelemetry::instance().increment_normal_served();
                break;
        }

        // OS Concurrency Control: Per-Train Mutual Exclusion
        std::mutex& train_mtx = get_train_mutex(req.train_number);

        // Check for lock contention to demonstrate OS race prevention telemetry
        if (!train_mtx.try_lock()) {
            SystemTelemetry::instance().increment_contention();
            train_mtx.lock(); // Block until train lock is released
        }

        BookingResult result;
        try {
            result = db_mgr_.execute_booking(req, worker_id);
        } catch (const std::exception& e) {
            result.success = false;
            result.status = BookingStatus::REJECTED;
            result.message = "Exception during reservation: " + std::string(e.what());
        }

        // Unlock train critical section
        train_mtx.unlock();

        // Deliver result to calling thread / HTTP request
        if (req.result_promise) {
            req.result_promise->set_value(result);
        }
    }
}

} // namespace railway
