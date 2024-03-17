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
	INFO("ts: " << ts);
	REQUIRE(ts.length() == 23);

	std::regex pattern(R"(\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3})");

	std::smatch match;
	ts = getTimeStr();
	REQUIRE(std::regex_search(ts, match, pattern));
}

TEST_CASE("TestCaptureLib_getTimeIsoStr",
		  "[capturelib][getTimeIsoStr]") {
	std::string ts = getTimeIsoStr();
	INFO("ts: " << ts);
	REQUIRE(ts.length() == 26);

	std::regex pattern(R"(\d{4}\-\d{2}\-\d{2}T\d{2}\:\d{2}\:\d{2}\.\d{6})");

	std::smatch match;
	ts = getTimeIsoStr();
	INFO("ts: " << ts);
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

// test for getAudioInNameByAlias
TEST_CASE("TestCaptureLib_getAudioInNameByAlias",
		  "[capturelib][getAudioInNameByAlias]") {
	std::string name = getAudioInNameByAlias("default");
	REQUIRE(name.length() == 0);

	name = getAudioInNameByAlias("line-in");
	REQUIRE(name.length() >0 );

	name = getAudioInNameByAlias("hdmi");
	REQUIRE(name.length() >0 );
}

// test for parseAudioVolume
TEST_CASE("TestCaptureLib_parseAudioVolume",
		  "[capturelib][parseAudioVolume]") {
	AudioVolume av = parseAudioVolume("0%");
	REQUIRE(av.label == "0%");
	REQUIRE(av.level == 0.0f);
	REQUIRE(av.unit == VolumeLevelUnit::PERCENT);

	av = parseAudioVolume("57.1%");
	REQUIRE(av.label == "57.1%");
	REQUIRE(av.level == 57.1f);
	REQUIRE(av.unit == VolumeLevelUnit::PERCENT);

	av = parseAudioVolume("86");
	REQUIRE(av.label == "86");
	REQUIRE(av.level == 86.0f);
	REQUIRE(av.unit == VolumeLevelUnit::RAW);

	av = parseAudioVolume("80.2dB");
	REQUIRE(av.label == "80.2dB");
	REQUIRE(av.level == 80.2f);
	REQUIRE(av.unit == VolumeLevelUnit::DB);

	// check parseAudioVolume with invalid inputs
	REQUIRE_THROWS_AS(parseAudioVolume("-1%"), std::runtime_error);
	REQUIRE_THROWS_AS(parseAudioVolume("102%"), std::runtime_error);
	REQUIRE_THROWS_AS(parseAudioVolume("95W"), std::runtime_error);
}