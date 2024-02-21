#define CATCH_CONFIG_MAIN
#include <iostream>
#include <atomic>
#include <thread>
#include <sysexits.h>
#include <getopt.h>
#include "ScreenCapture.h"
#include <catch2/catch.hpp>

// Function to test
int add(int a, int b) {
	return a + b;
}

TEST_CASE("TestScreenCapture_add", "[add]") {
	// Test case 1
	REQUIRE(add(2, 2) == 4);

	// Test case 2
	REQUIRE(add(-1, 1) == 0);
}