#define CATCH_CONFIG_MAIN
#include "reprostim/CaptureLib.h"
#include <catch2/catch.hpp>

using namespace reprostim;
// Function to test
int add(int a, int b) {
	return a + b;
}

TEST_CASE("TestCaptureLib_add",
		  "[capturelib][add]") {
	// Test case 1
	REQUIRE(add(1, 2) == 3);

	// Test case 2
	REQUIRE(add(3, 5) == 8);
}

TEST_CASE("TestCaptureLib_getTimeStr",
		  "[capturelib][getTimeStr]") {
	std::string ts = getTimeStr();
	REQUIRE(ts.length() == 23);

	std::regex pattern(R"(\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3})");

	std::smatch match;
	ts = getTimeStr();
	REQUIRE(std::regex_search(ts, match, pattern));
}

// test for isSysBreakExec
TEST_CASE("TestCaptureLib_isSysBreakExec",
		  "[capturelib][isSysBreakExec]") {
	REQUIRE(isSysBreakExec() == false);
	setSysBreakExec(true);
	REQUIRE(isSysBreakExec() == true);
	setSysBreakExec(false);
}

// test for mmwcSdkVersion
TEST_CASE("TestCaptureLib_mwcSdkVersion",
		  "[capturelib][mwcSdkVersion]") {
	std::string version = mwcSdkVersion();
	REQUIRE(version.length() > 0);
	REQUIRE(version == "3.3.1313");
}

// test for checkOutDir
TEST_CASE("TestCaptureLib_checkOutDir",
		  "[capturelib][checkOutDir]") {
	std::string outDir = "/tmp";
	REQUIRE(checkOutDir(outDir) == true);
}

// test for currentTimeMs
TEST_CASE("TestCaptureLib_currentTimeMs",
		  "[capturelib][currentTimeMs]") {
	auto t1 = currentTimeMs();
	SLEEP_MS(20);
	auto t2 = currentTimeMs();
	REQUIRE((t2 - t1) >= 20);
}