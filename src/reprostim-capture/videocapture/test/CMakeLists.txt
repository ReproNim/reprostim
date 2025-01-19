# CTests for videocapture project
project(reprostim-videocapture-tests)

set(APP_SRC ${PROJECT_SOURCE_DIR}/../src)

add_executable(${PROJECT_NAME}
        TestVideoCapture.cpp
        ${APP_SRC}/VideoCapture.cpp
)

target_link_libraries(
        ${PROJECT_NAME}
        capturelib
        Catch2::Catch2WithMain
)

target_include_directories(${PROJECT_NAME}
        PUBLIC
        ${APP_SRC}
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