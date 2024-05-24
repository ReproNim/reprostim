# CMakeLists.txt (videocapture project)

project(reprostim-videocapture)

# Create the executable
add_executable(${PROJECT_NAME}
        src/VideoCapture.cpp
        src/main.cpp
)
# Copy config.yaml to out folder as well
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.yaml ${CMAKE_CURRENT_BINARY_DIR}/config.yaml COPYONLY)

# Install the executable to /usr/local/bin
install(TARGETS reprostim-videocapture
        RUNTIME DESTINATION ${CAPTURE_INSTALL_DIR})

target_include_directories(${PROJECT_NAME} PUBLIC "Include")

target_link_libraries(${PROJECT_NAME}
        capturelib
        )