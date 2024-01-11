# CMakeLists.txt (screencapture project)

project(reprostim-screencapture)


# Create the executable
add_executable(${PROJECT_NAME} ScreenCapture.cpp)

target_link_libraries(${PROJECT_NAME}
        capturelib
)