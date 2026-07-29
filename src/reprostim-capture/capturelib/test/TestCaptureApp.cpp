#include <filesystem>
#include <fstream>
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

// test for parseUsbScanMode
TEST_CASE("TestCaptureApp_parseUsbScanMode",
		  "[capturelib][CaptureApp][parseUsbScanMode]") {
	REQUIRE(parseUsbScanMode("") == UsbScanMode::DEFAULT);
	REQUIRE(parseUsbScanMode("poll") == UsbScanMode::POLL);
	REQUIRE(parseUsbScanMode("hotplug") == UsbScanMode::HOTPLUG);
	REQUIRE(parseUsbScanMode("invalid") == UsbScanMode::UNKNOWN);
	REQUIRE(parseUsbScanMode("POLL") == UsbScanMode::UNKNOWN); // case-sensitive
	// DEFAULT is an alias for POLL, not a distinct mode
	REQUIRE(UsbScanMode::DEFAULT == UsbScanMode::POLL);
}

// test for AppConfig default usb_scan_mode value
TEST_CASE("TestCaptureApp_AppConfig_usbScanMode_default",
		  "[capturelib][CaptureApp][AppConfig][usb_scan_mode]") {
	AppConfig cfg;
	REQUIRE(cfg.usb_scan_mode == UsbScanMode::DEFAULT);
}

// Test-only subclass exposing protected USB-scan state so checkUsbScan(),
// onUsbDevArrived() and onUsbDevLeft() can be exercised deterministically
// without a full run() (hardware init, config load, blocking loop).
class TestCaptureAppImpl: public CaptureApp {
public:
	TestCaptureAppImpl() {
		// avoid touching an uninitialized pRepromonQueue via _NOTIFY_REPROMON,
		// which is otherwise only set up as part of run()
		fRepromonEnabled = false;
	}
	void setUsbScanMode(UsbScanMode mode) { cfg.usb_scan_mode = mode; }
	void setUsbScanCount(int count) { usbScanCount = count; }
	int getUsbScanCount() const { return usbScanCount.load(); }
	void setLastUsbScanTime(long long ms) { lastUsbScanTime = ms; }
	long long getLastUsbScanTime() const { return lastUsbScanTime; }
};

// test for checkUsbScan in POLL mode
TEST_CASE("TestCaptureApp_checkUsbScan_pollMode",
		  "[capturelib][CaptureApp][checkUsbScan]") {
	TestCaptureAppImpl app;
	app.setUsbScanMode(UsbScanMode::POLL);

	// POLL mode always allows a scan, regardless of retry count
	app.setUsbScanCount(0);
	REQUIRE(app.checkUsbScan() == true);

	app.setUsbScanCount(1000);
	REQUIRE(app.checkUsbScan() == true);
}

// test for checkUsbScan in HOTPLUG mode, within the initial retry burst
TEST_CASE("TestCaptureApp_checkUsbScan_hotplugMode_withinRetryBurst",
		  "[capturelib][CaptureApp][checkUsbScan]") {
	TestCaptureAppImpl app;
	app.setUsbScanMode(UsbScanMode::HOTPLUG);

	app.setUsbScanCount(0);
	REQUIRE(app.checkUsbScan() == true);

	// boundary: exactly at the retry count threshold is still allowed ("<=")
	app.setUsbScanCount(USB_SCAN_HOTPLUG_RETRY_COUNT);
	REQUIRE(app.checkUsbScan() == true);
}

// test for checkUsbScan in HOTPLUG mode, retry burst exceeded but the
// throttling interval has not elapsed yet since the last scan
TEST_CASE("TestCaptureApp_checkUsbScan_hotplugMode_exceedsRetry_withinInterval",
		  "[capturelib][CaptureApp][checkUsbScan]") {
	TestCaptureAppImpl app;
	app.setUsbScanMode(UsbScanMode::HOTPLUG);
	app.setUsbScanCount(USB_SCAN_HOTPLUG_RETRY_COUNT + 1);
	app.setLastUsbScanTime(currentTimeMs());

	REQUIRE(app.checkUsbScan() == false);
}

// test for checkUsbScan in HOTPLUG mode, retry burst exceeded and the
// throttling interval has elapsed since the last scan
TEST_CASE("TestCaptureApp_checkUsbScan_hotplugMode_exceedsRetry_intervalElapsed",
		  "[capturelib][CaptureApp][checkUsbScan]") {
	TestCaptureAppImpl app;
	app.setUsbScanMode(UsbScanMode::HOTPLUG);
	app.setUsbScanCount(USB_SCAN_HOTPLUG_RETRY_COUNT + 1);
	app.setLastUsbScanTime(currentTimeMs() - USB_SCAN_HOTPLUG_INTERVAL_MS - 1000);

	REQUIRE(app.checkUsbScan() == true);
}

// test for checkUsbScan when usb_scan_mode is UNKNOWN (defensive: never scan)
TEST_CASE("TestCaptureApp_checkUsbScan_unknownMode",
		  "[capturelib][CaptureApp][checkUsbScan]") {
	TestCaptureAppImpl app;
	app.setUsbScanMode(UsbScanMode::UNKNOWN);
	app.setUsbScanCount(0);

	REQUIRE(app.checkUsbScan() == false);
}

// test for onUsbDevArrived/onUsbDevLeft resetting the USB scan retry count
TEST_CASE("TestCaptureApp_onUsbDev_resetsUsbScanCount",
		  "[capturelib][CaptureApp][onUsbDevArrived][onUsbDevLeft]") {
	TestCaptureAppImpl app;

	app.setUsbScanCount(USB_SCAN_HOTPLUG_RETRY_COUNT + 5);
	REQUIRE(app.getUsbScanCount() == USB_SCAN_HOTPLUG_RETRY_COUNT + 5);
	app.onUsbDevArrived("/dev/test_video0");
	REQUIRE(app.getUsbScanCount() == 0);

	app.setUsbScanCount(USB_SCAN_HOTPLUG_RETRY_COUNT + 5);
	app.onUsbDevLeft("/dev/test_video0");
	REQUIRE(app.getUsbScanCount() == 0);
}

// test for loadConfig parsing of usb_scan_mode from config.yaml
TEST_CASE("TestCaptureApp_loadConfig_usbScanMode",
		  "[capturelib][CaptureApp][loadConfig][usb_scan_mode]") {
	CaptureApp app;
	std::string fileName = "reprostim_test_captureapp_usb_scan_mode_" + getTimeStr() + ".yaml";
	std::filesystem::path yamlPath = std::filesystem::temp_directory_path() / fileName;

	auto writeYaml = [&](const std::string& content) {
		std::ofstream out(yamlPath);
		out << content;
		out.close();
	};

	// not specified -> defaults to POLL
	writeYaml("---\ndevice_serial_number: \"auto\"\n");
	AppConfig cfgDefault;
	REQUIRE(app.loadConfig(cfgDefault, yamlPath.string()) == true);
	REQUIRE(cfgDefault.usb_scan_mode == UsbScanMode::POLL);

	// explicit "poll"
	writeYaml("---\nusb_scan_mode: \"poll\"\n");
	AppConfig cfgPoll;
	REQUIRE(app.loadConfig(cfgPoll, yamlPath.string()) == true);
	REQUIRE(cfgPoll.usb_scan_mode == UsbScanMode::POLL);

	// explicit "hotplug"
	writeYaml("---\nusb_scan_mode: \"hotplug\"\n");
	AppConfig cfgHotplug;
	REQUIRE(app.loadConfig(cfgHotplug, yamlPath.string()) == true);
	REQUIRE(cfgHotplug.usb_scan_mode == UsbScanMode::HOTPLUG);

	// invalid value -> loadConfig fails
	writeYaml("---\nusb_scan_mode: \"bogus\"\n");
	AppConfig cfgInvalid;
	REQUIRE(app.loadConfig(cfgInvalid, yamlPath.string()) == false);

	if( std::filesystem::exists(yamlPath) ) {
		std::filesystem::remove(yamlPath);
	}
}