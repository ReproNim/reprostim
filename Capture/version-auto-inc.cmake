#
# CMake script to auto-increment build number in a file
#
# Usage : cmake -P version-auto-inc.cmake
#
# where version file is "version.txt" in the current directory
#

cmake_minimum_required(VERSION 3.10)
set(VERSION_FILE "version.txt")

message(STATUS "Auto-increment build number in \"${VERSION_FILE}\" file")

if(EXISTS ${VERSION_FILE})
  file(READ ${VERSION_FILE} VERSION_TXT)
  message(STATUS "Old version : ${VERSION_TXT}")
  string(REGEX MATCH "([0-9]+)\\.([0-9]+)\\.([0-9]+)\\.([0-9]+)" VERSION_MATCH "${VERSION_TXT}")
  set(VERSION_BUILD ${CMAKE_MATCH_4})
  math(EXPR VERSION_BUILD "${VERSION_BUILD}+1")
  set(VERSION_TXT "${CMAKE_MATCH_1}.${CMAKE_MATCH_2}.${CMAKE_MATCH_3}.${VERSION_BUILD}")
else()
  message(STATUS "Version file not found : ${VERSION_FILE}")
  set(VERSION_TXT "0.0.0.0")
endif()

file(WRITE ${VERSION_FILE} ${VERSION_TXT})
message(STATUS "New version : ${VERSION_TXT}")

