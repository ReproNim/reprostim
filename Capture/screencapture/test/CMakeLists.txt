# CTests for screencapture project
project(reprostim-screencapture-tests)

set(APP_SRC ${PROJECT_SOURCE_DIR}/../src)

add_executable(${PROJECT_NAME}
        TestScreenCapture.cpp
        ${APP_SRC}/RecordingThread.cpp
        ${APP_SRC}/ScreenCapture.cpp
)

target_link_libraries(
        ${PROJECT_NAME}
        capturelib
        opencv_core
        opencv_highgui
        opencv_imgcodecs
        Catch2::Catch2
)

find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

target_include_directories(${PROJECT_NAME}
        PUBLIC
        ${APP_SRC}
)


include(CTest)
include(Catch)
catch_discover_tests(${PROJECT_NAME})

# add also a test for the help message
add_test(NAME TestScreenCapture_help
        COMMAND reprostim-screencapture -h)

# Optionally, set properties for the test
set_tests_properties(TestScreenCapture_help
        PROPERTIES
        PASS_REGULAR_EXPRESSION "Usage\\: reprostim-screencapture.*"
        WILL_FAIL FALSE
        EXPECTED_RETURN_CODE 0
)
