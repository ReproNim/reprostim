#ifndef CAPTURE_SCREENCAPTURE_H
#define CAPTURE_SCREENCAPTURE_H

#include "CaptureApp.h"
#include "RecordingThread.h"

///////////////////////////////////////////////////////////////////////////
//
using namespace reprostim;

// Specific options for ScreenCaptureApp
struct ScreenCaptureOpts {
	bool dump_raw;
	int  interval_ms;
	int  threshold;
};

class ScreenCaptureApp: public CaptureApp {
private:
	RecordingThread*  m_prtCur;
	RecordingThread*  m_prtPrev;
	ScreenCaptureOpts m_scOpts;
public:
	ScreenCaptureApp();
	~ScreenCaptureApp();
	void onCaptureStart() override;
	void onCaptureStop(const std::string& message) override;
	bool onLoadConfig(AppConfig &cfg, const std::string &pathConfig, YAML::Node doc) override;
	int  parseOpts(AppOpts& opts, int argc, char* argv[]) override;
};

#endif //CAPTURE_SCREENCAPTURE_H
