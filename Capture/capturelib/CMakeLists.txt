# CMakeLists.txt (capturelib project)
project (capturelib)

# version header generator
configure_file(${PROJECT_SOURCE_DIR}/include/reprostim/CaptureVer.h.in
        ${PROJECT_SOURCE_DIR}/include/reprostim/CaptureVer.h
)

add_library(${PROJECT_NAME} STATIC
        src/CaptureLib.cpp
        src/CaptureLog.cpp
        src/CaptureRepromon.cpp
        src/CaptureApp.cpp
        include/reprostim/CaptureVer.h.in
)
add_library(reprostim::capturelib ALIAS ${PROJECT_NAME})

target_include_directories(${PROJECT_NAME}
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
)

target_link_libraries(${PROJECT_NAME}
        PUBLIC
            MWCapture
            pthread
            dl
            udev
            asound
            v4l2
            yaml-cpp
            spdlog
            fmt
        )
