# CMakeLists.txt (screencapture project)

project(reprostim-screencapture)

# Create the executable
add_executable(${PROJECT_NAME}
        src/RecordingThread.cpp
        src/ScreenCapture.cpp
        src/main.cpp
)
# Copy config.yaml to out folder as well
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.yaml ${CMAKE_CURRENT_BINARY_DIR}/config.yaml COPYONLY)

find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

target_include_directories(${PROJECT_NAME} PUBLIC "Include")

target_link_libraries(${PROJECT_NAME}
        capturelib
        opencv_core
        opencv_highgui
        opencv_imgcodecs
)