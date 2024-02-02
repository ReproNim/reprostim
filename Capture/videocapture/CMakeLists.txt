# CMakeLists.txt (videocapture project)

project(reprostim-videocapture)

# Create the executable
add_executable(${PROJECT_NAME}
        VideoCapture.cpp
        main.cpp
)
# Copy config.yaml to out folder as well
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.yaml ${CMAKE_CURRENT_BINARY_DIR}/config.yaml COPYONLY)


target_include_directories(${PROJECT_NAME} PUBLIC "Include")

target_link_libraries(${PROJECT_NAME}
        capturelib
        )