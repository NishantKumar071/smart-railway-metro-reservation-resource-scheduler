cmake_minimum_required(VERSION 3.15)
project(SmartRailwayScheduler LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    "C:/Program Files/MySQL/MySQL Server 8.0/include"
)

link_directories(
    "C:/Program Files/MySQL/MySQL Server 8.0/lib"
)

# Common sources
set(COMMON_SOURCES
    src/db_manager.cpp
    src/scheduler.cpp
    src/telemetry.cpp
)

# Main Executable
add_executable(smart_railway src/main.cpp ${COMMON_SOURCES})
target_link_libraries(smart_railway PRIVATE libmysql ws2_32 crypt32)

# Test Executable
add_executable(concurrency_test tests/concurrency_test.cpp ${COMMON_SOURCES})
target_link_libraries(concurrency_test PRIVATE libmysql ws2_32 crypt32)
