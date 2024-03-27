# CMakeLists.txt (Main Capture project)
cmake_minimum_required (VERSION 3.10)

project(Capture)

option(CTEST_ENABLED "Specify CTest build and run are enabled" ON)

# hook to reload version.txt file
set(CAPTURE_VERSION_FILE "${CMAKE_CURRENT_SOURCE_DIR}/version.txt")
configure_file(${CAPTURE_VERSION_FILE}
        "${CMAKE_BINARY_DIR}/version.txt" COPYONLY)

set(CMAKE_CXX_STANDARD 20)

# version info
set(CAPTURE_VERSION_MAJOR 0)
set(CAPTURE_VERSION_MINOR 0)
set(CAPTURE_VERSION_PATCH 0)
set(CAPTURE_VERSION_BUILD 0)
set(CAPTURE_BUILD_TYPE ${CMAKE_BUILD_TYPE})
# Set CAPTURE_BUILD_TYPE to "Release" if it's empty or an empty string
if(NOT CAPTURE_BUILD_TYPE OR CAPTURE_BUILD_TYPE STREQUAL "")
    set(CAPTURE_BUILD_TYPE "Release")
endif()

# load version from version.txt file if any
if(EXISTS ${CAPTURE_VERSION_FILE})
    file(READ ${CAPTURE_VERSION_FILE} CAPTURE_VERSION_TXT)
    # parse version
    string(REGEX MATCH "([0-9]+)\\.([0-9]+)\\.([0-9]+)\\.([0-9]+)" CAPTURE_VERSION_MATCH "${CAPTURE_VERSION_TXT}")
    set(CAPTURE_VERSION_MAJOR "${CMAKE_MATCH_1}")
    set(CAPTURE_VERSION_MINOR "${CMAKE_MATCH_2}")
    set(CAPTURE_VERSION_PATCH "${CMAKE_MATCH_3}")
    set(CAPTURE_VERSION_BUILD "${CMAKE_MATCH_4}")
endif()

set(CAPTURE_VERSION_STRING "${CAPTURE_VERSION_MAJOR}.${CAPTURE_VERSION_MINOR}.${CAPTURE_VERSION_PATCH}.${CAPTURE_VERSION_BUILD}")
# Append "d" to CAPTURE_VERSION_STRING if build type is Debug
if(CAPTURE_BUILD_TYPE STREQUAL "Debug")
    set(CAPTURE_VERSION_STRING "${CAPTURE_VERSION_STRING}d")
endif()

string(TIMESTAMP CAPTURE_VERSION_DATE "%Y-%m-%d %H:%M:%S")
execute_process(
        COMMAND git describe --tags --always
        OUTPUT_VARIABLE CAPTURE_VERSION_TAG
        OUTPUT_STRIP_TRAILING_WHITESPACE
)

# ARCH:=$(shell uname -m)
set(ARCH x64)
set(MWCAPTURE_SDK_HOME 3rdparty/MWCapture_SDK_Linux-3_3_1_1313)

# Add MWCapture SDK include/lib paths
include_directories(${MWCAPTURE_SDK_HOME}/Include)
link_directories(${MWCAPTURE_SDK_HOME}/Lib/${ARCH})

# Add projects
add_subdirectory(capturelib)
add_subdirectory(screencapture)
add_subdirectory(videocapture)

# Add tests optionally
if(CTEST_ENABLED)
    message(STATUS "CTests are ENABLED")
    enable_testing()

    find_package(Catch2 REQUIRED)
    include_directories(${Catch2_INCLUDE_DIRS})

    add_subdirectory(test)
    add_subdirectory(capturelib/test)
    add_subdirectory(screencapture/test)
    add_subdirectory(videocapture/test)
else()
    message(STATUS "CTests are DISABLED")
endif()
