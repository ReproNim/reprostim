#define CATCH_CONFIG_MAIN
#include <iostream>
#include <atomic>
#include <thread>
#include <sysexits.h>
#include <getopt.h>
#include "VideoCapture.h"
#include <catch2/catch.hpp>

// Function to test
int add(int a, int b) {
	return a + b;
}

TEST_CASE("TestVideoCapture_add", "[add]") {
	// Test case 1
	REQUIRE(add(5, 3) == 8);

	// Test case 2
	REQUIRE(add(-10, 20) == 10);
}