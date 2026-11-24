#pragma once
#include "models.h"
#include <queue>
#include <vector>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <future>
#include <memory>
#include <functional>

namespace smartrail {

struct PrioritizedTask {
    PriorityLevel priority;
    std::chrono::steady_clock::time_point arrival_time;
    std::string request_id;
    BookingRequestData data;
    std::shared_ptr<std::promise<BookingResult>> result_promise;

    // Min-heap ordering: higher priority (lower enum value) first, then older arrival time, then request_id
    bool operator>(const PrioritizedTask& other) const {
        if (priority != other.priority) {
            return static_cast<int>(priority) > static_cast<int>(other.priority);
        }
        if (arrival_time != other.arrival_time) {
            return arrival_time > other.arrival_time;
        }
        return request_id > other.request_id;
    }
};

class PriorityScheduler {
public:
    PriorityScheduler(int num_workers = 6, int max_queue_size = 100);
    ~PriorityScheduler();

    void start();
    void stop();

    std::future<BookingResult> submit_booking(const BookingRequestData& data);

    int get_queue_size();
    int get_worker_count() const { return num_workers_; }

private:
    void worker_thread_loop(int worker_id);

    int num_workers_;
    int max_queue_size_;
    std::atomic<bool> is_running_{false};

    // Synchronization primitives
    // Lock acquisition order:
    // 1. queue_mutex_ is the sole lock protecting the priority queue (deadlock prevention rule: no nested locks)
    std::mutex queue_mutex_;
    std::condition_variable cv_not_empty_;
    std::condition_variable cv_not_full_;

    std::priority_queue<PrioritizedTask, std::vector<PrioritizedTask>, std::greater<PrioritizedTask>> task_queue_;
    std::vector<std::thread> workers_;
};

} // namespace smartrail
