# CTests for videocapture project
project(reprostim-videocapture-tests)

add_executable(${PROJECT_NAME}
        TestVideoCapture.cpp
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

add_test(NAME TestVideoCapture_help
        COMMAND reprostim-videocapture -h)

# Optionally, set properties for the test
set_tests_properties(TestVideoCapture_help
        PROPERTIES
        PASS_REGULAR_EXPRESSION "Usage\\: reprostim-videocapture.*"
        WILL_FAIL FALSE
        EXPECTED_RETURN_CODE 78
)