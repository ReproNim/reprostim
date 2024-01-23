#ifndef CAPTURE_SCREENCAPTURE_H
#define CAPTURE_SCREENCAPTURE_H

#include "CaptureApp.h"
///////////////////////////////////////////////////////////////////////////
//
using namespace reprostim;

class ScreenCaptureApp: public CaptureApp {
public:
	ScreenCaptureApp();
	void onCaptureStart() override;
	void onCaptureStop(const std::string& message) override;
	int  parseOpts(AppOpts& opts, int argc, char* argv[]) override;
};

#endif //CAPTURE_SCREENCAPTURE_H
