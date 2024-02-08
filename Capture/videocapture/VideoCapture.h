#ifndef CAPTURE_VIDEOCAPTURE_H
#define CAPTURE_VIDEOCAPTURE_H

#include "CaptureApp.h"
#include "CaptureThreading.h"

///////////////////////////////////////////////////////////////////////////
//
using namespace reprostim;

// ffmpeg params shared between threads
// make sure it's thread-safe in usage
struct FfmpegParams {
	const bool        verbose;
	const std::string cmd;
	const std::string outExt;
	const std::string outPath;
	const std::string outVideoFile;
	const std::string start_ts;
};

using FfmpegThread = WorkerThread<FfmpegParams>;

class VideoCaptureApp: public CaptureApp {
private:
	SingleThreadExecutor<FfmpegThread> m_ffmpegExec;

	std::string startRecording(int cx, int cy, const std::string& frameRate, const std::string& outPath,
							   const std::string& v_dev, const std::string& a_dev);
	void stopRecording(const std::string& start_ts, const std::string& vpath);
public:
	VideoCaptureApp();
	~VideoCaptureApp();

	//
	void onCaptureStart() override;
	void onCaptureStop(const std::string& message) override;
	int  parseOpts(AppOpts& opts, int argc, char* argv[]) override;
};

#endif //CAPTURE_VIDEOCAPTURE_H
