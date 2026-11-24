cmake_minimum_required(VERSION 3.15)
project(SmartRail_AI_Plus VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/vendor
)

# Source files
set(SOURCES
    src/main.cpp
    src/scheduler.cpp
    src/booking_engine.cpp
    src/telemetry.cpp
    src/db_connection.cpp
)

# Headers
set(HEADERS
    include/config.h
    include/models.h
    include/scheduler.h
    include/booking_engine.h
    include/telemetry.h
    include/db_connection.h
)

# Executable
add_executable(smartrail_backend ${SOURCES} ${HEADERS})

# Find Threads
find_package(Threads REQUIRED)
target_link_libraries(smartrail_backend PRIVATE Threads::Threads)

# Optional MySQL support if installed
find_package(MySQL QUIET)
if(MySQL_FOUND)
    target_include_directories(smartrail_backend PRIVATE ${MySQL_INCLUDE_DIRS})
    target_link_libraries(smartrail_backend PRIVATE ${MySQL_LIBRARIES})
    target_compile_definitions(smartrail_backend PRIVATE HAVE_MYSQL=1)
endif()

# Windows specific socket libraries for httplib
if(WIN32)
    target_link_libraries(smartrail_backend PRIVATE ws2_32 wsock32 crypt32)
endif()

# Enable compiler warnings
if(MSVC)
    target_compile_options(smartrail_backend PRIVATE /W4)
else()
    target_compile_options(smartrail_backend PRIVATE -Wall -Wextra -pthread)
endif()
