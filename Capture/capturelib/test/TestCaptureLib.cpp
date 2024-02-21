#define CATCH_CONFIG_MAIN
#include "reprostim/CaptureLib.h"
#include <catch2/catch.hpp>

// Function to test
int add(int a, int b) {
	return a + b;
}

TEST_CASE("capturelib_add_test", "[add]") {
	// Test case 1
	REQUIRE(add(1, 2) == 3);

	// Test case 2
	REQUIRE(add(3, 5) == 8);
}