#define CATCH_CONFIG_MAIN
#include <iostream>
#include <atomic>
#include <thread>
#include <sysexits.h>
#include <getopt.h>
#include "ScreenCapture.h"

// Catch2 v2/v3 includes
#if __has_include(<catch2/catch_all.hpp>)
    // Catch2 v3
    #include <catch2/catch_all.hpp>
#else
  // Catch2 v2 fallback
  #include <catch2/catch.hpp>
#endif

// Function to test
int add(int a, int b) {
	return a + b;
}

TEST_CASE("TestScreenCapture_add",
		  "[screencapture][add]") {
	// Test case 1
	REQUIRE(add(2, 2) == 4);

	// Test case 2
	REQUIRE(add(-1, 1) == 0);
}

TEST_CASE("TestScreenCapture_constructor_destructor",
		  "[screencapture][ScreenCaptureApp][constructor][destructor]") {
	std::unique_ptr<ScreenCaptureApp> pApp(new ScreenCaptureApp());
	REQUIRE(pApp != nullptr);

	pApp = nullptr;
	REQUIRE(pApp == nullptr);
}