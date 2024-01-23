#ifndef CAPTURE_VIDEOCAPTURE_H
#define CAPTURE_VIDEOCAPTURE_H

#include "CaptureApp.h"

///////////////////////////////////////////////////////////////////////////
//
using namespace reprostim;

class VideoCaptureApp: public CaptureApp {
public:
	VideoCaptureApp();
	void onCaptureStart() override;
	void onCaptureStop(const std::string& message) override;
	int  parseOpts(AppOpts& opts, int argc, char* argv[]) override;
	std::string startRecording(int cx, int cy, const std::string& frameRate, const std::string& outPath,
							   const std::string& v_dev, const std::string& a_dev);
	void stopRecording(const std::string& start_ts, const std::string& vpath);
};

#endif //CAPTURE_VIDEOCAPTURE_H
