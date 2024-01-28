#ifndef CAPTURE_SCREENCAPTURE_H
#define CAPTURE_SCREENCAPTURE_H

#include "CaptureApp.h"
#include "RecordingThread.h"

///////////////////////////////////////////////////////////////////////////
//
using namespace reprostim;

class ScreenCaptureApp: public CaptureApp {
private:
	RecordingThread* m_prtCur;
	RecordingThread* m_prtPrev;
public:
	ScreenCaptureApp();
	~ScreenCaptureApp();
	void onCaptureStart() override;
	void onCaptureStop(const std::string& message) override;
	int  parseOpts(AppOpts& opts, int argc, char* argv[]) override;
};

#endif //CAPTURE_SCREENCAPTURE_H
