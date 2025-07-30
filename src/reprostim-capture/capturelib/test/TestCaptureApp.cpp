#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureApp.h"

// Catch2 v2/v3 includes
#if __has_include(<catch2/catch_all.hpp>)
    // Catch2 v3
    #include <catch2/catch_all.hpp>
#else
  // Catch2 v2 fallback
  #include <catch2/catch.hpp>
#endif

using namespace reprostim;

// test for CaptureApp
TEST_CASE("TestCaptureApp_constructor_destructor",
		  "[capturelib][CaptureApp][constructor][destructor]") {
	std::unique_ptr<CaptureApp> pApp = std::make_unique<CaptureApp>();
	REQUIRE(pApp != nullptr);
	pApp = nullptr;
}
