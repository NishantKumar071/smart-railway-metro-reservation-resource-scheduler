#pragma once
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <unordered_map>
#include <memory>
#include <atomic>
#include <future>
#include "models.h"
#include "db_manager.h"

namespace railway {

class ResourceScheduler {
public:
    ResourceScheduler(DatabaseManager& db_mgr, size_t worker_threads = 6);
    ~ResourceScheduler();

    // OS Producer Method: Enqueues request into priority queue
    std::future<BookingResult> enqueue_booking(BookingRequest request);

    // Synchronous execution shortcut if needed
    BookingResult execute_immediate_cancellation(const std::string& pnr);

    // Stop and join workers
    void shutdown();

    size_t get_queue_size();
    size_t get_worker_count() const { return worker_count_; }

private:
    // OS Consumer Worker Loop
    void worker_loop(int worker_id);

    // Per-train mutual exclusion lock
    std::mutex& get_train_mutex(const std::string& train_number);

    DatabaseManager& db_mgr_;
    size_t worker_count_;
    std::vector<std::thread> workers_;

    // OS Priority Queue (Bounded / Thread-Safe)
    std::priority_queue<BookingRequest, std::vector<BookingRequest>, BookingPriorityComparator> priority_queue_;
    std::mutex queue_mutex_;
    std::condition_variable cv_queue_;
    std::atomic<bool> is_running_{true};

    // Fine-grained per-train mutexes (Preventing double-booking race conditions)
    std::mutex train_map_mutex_;
    std::unordered_map<std::string, std::unique_ptr<std::mutex>> train_mutexes_;
};

} // namespace railway
