# CTests for screencapture project
project(reprostim-screencapture-tests)

add_executable(${PROJECT_NAME}
        TestScreenCapture.cpp
)

target_link_libraries(
        ${PROJECT_NAME}
        capturelib
        Catch2::Catch2
)

target_include_directories(${PROJECT_NAME}
        PUBLIC
        ${PROJECT_SOURCE_DIR}/../src
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
