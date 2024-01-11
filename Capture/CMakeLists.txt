# CMakeLists.txt (Main Capture project)
cmake_minimum_required (VERSION 3.10)

project(Capture)

set(CMAKE_CXX_STANDARD 17)

# ARCH:=$(shell uname -m)
set(ARCH x64)
set(MWCAPTURE_SDK_HOME 3rdparty/MWCapture_SDK_Linux-3_3_1_1313)

# Add MWCapture SDK include/lib paths
include_directories(${MWCAPTURE_SDK_HOME}/Include)
link_directories(${MWCAPTURE_SDK_HOME}/Lib/${ARCH})

# Add projects
add_subdirectory(capturelib)
add_subdirectory(screencapture)
add_subdirectory(videocapture)