# CTests for capturelib project

project(reprostim-capturelib-tests)

add_executable(${PROJECT_NAME}
    TestCaptureLib.cpp
    TestCaptureLog.cpp
    TestCaptureThreading.cpp
    TestCaptureRest.cpp
    TestCaptureRepromon.cpp
    TestCaptureApp.cpp
)

if(CATCH2_VERSION EQUAL 2)
    target_link_libraries(
            ${PROJECT_NAME}
            capturelib
            Catch2::Catch2
    )
else()
    target_link_libraries(
            ${PROJECT_NAME}
            capturelib
            Catch2::Catch2WithMain
    )
endif()

include(CTest)
include(Catch)
catch_discover_tests(${PROJECT_NAME})
