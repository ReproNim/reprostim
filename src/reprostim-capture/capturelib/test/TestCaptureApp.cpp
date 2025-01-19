#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureApp.h"
#include <catch2/catch_all.hpp>

using namespace reprostim;

// test for CaptureApp
TEST_CASE("TestCaptureApp_constructor_destructor",
		  "[capturelib][CaptureApp][constructor][destructor]") {
	std::unique_ptr<CaptureApp> pApp = std::make_unique<CaptureApp>();
	REQUIRE(pApp != nullptr);
	pApp = nullptr;
}
