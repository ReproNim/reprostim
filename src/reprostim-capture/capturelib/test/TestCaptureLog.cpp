#include <iostream>
#include <fstream>
#include <filesystem>
#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureLog.h"
#include <catch2/catch_all.hpp>

using namespace reprostim;

// test case for FileLogger
TEST_CASE("TestCaptureLog_FileLogger",
		  "[capturelib][CaptureLog][FileLogger]") {
	FileLogger logger;
	std::string fileName = "reprostim_test_capturelog_"+getTimeStr() + ".log";
	std::filesystem::path logPath = std::filesystem::temp_directory_path() / fileName;
	logger.open("test", logPath, LogLevel::INFO);
	REQUIRE(logger.getName() == "test");
	REQUIRE(logger.getFilePath() == logPath.string());
	REQUIRE(logger.isDebugEnabled() == false);
	REQUIRE(logger.isErrorEnabled() == true);
	REQUIRE(logger.isInfoEnabled() == true);
	REQUIRE(logger.isWarnEnabled() == true);
	logger.debug_("debug message");
	logger.info("info message");
	logger.warn("warn message");
	logger.error("error message");
	logger.close();
	REQUIRE(std::filesystem::exists(logPath));
	if( std::filesystem::exists(logPath) ) {
		std::filesystem::remove(logPath);
	}
}