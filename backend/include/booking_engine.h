#pragma once
#include "models.h"
#include <string>

namespace smartrail {

class BookingEngine {
public:
    static BookingEngine& instance();

    // Core transaction-safe booking processor
    BookingResult process_booking(const BookingRequestData& req, int worker_id);

    // Core cancellation & waitlist promotion processor
    bool cancel_booking(const std::string& pnr, std::string& out_promoted_pnr);

    // Helpers
    std::string generate_unique_pnr();

private:
    BookingEngine() = default;
};

} // namespace smartrail
