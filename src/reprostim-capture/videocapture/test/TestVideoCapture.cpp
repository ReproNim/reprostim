#define CATCH_CONFIG_MAIN
#include <iostream>
#include <atomic>
#include <thread>
#include <sysexits.h>
#include <getopt.h>
#include "VideoCapture.h"
#include <catch2/catch_all.hpp>

// Function to test
int add(int a, int b) {
	return a + b;
}

TEST_CASE("TestVideoCapture_add",
		  "[videocapture][add]") {
	// Test case 1
	REQUIRE(add(5, 3) == 8);

	// Test case 2
	REQUIRE(add(-10, 20) == 10);
}

TEST_CASE("TestVideoCapture_constructor_destructor",
		  "[videocapture][VideoCaptureApp][constructor][destructor]") {
	std::unique_ptr<VideoCaptureApp> pApp(new VideoCaptureApp());
	REQUIRE(pApp != nullptr);

	pApp = nullptr;
	REQUIRE(pApp == nullptr);
}