#ifndef CAPTURE_VIDEOCAPTURE_H
#define CAPTURE_VIDEOCAPTURE_H

#include "reprostim/CaptureApp.h"
#include "reprostim/CaptureThreading.h"

///////////////////////////////////////////////////////////////////////////
//
using namespace reprostim;


// external proc params, make sure it's thread-safe in usage
// as shared between threads
struct ExtProcParams {
	const ExtProcOpts       opts; // passed all options by value
	const SessionLogger_ptr pLogger;
};


// ffmpeg params shared between threads
// make sure it's thread-safe in usage
struct FfmpegParams {
	const std::string       appName;
	const std::string       cmd;
	const std::string       ffmpeg_cmd;
	const std::string       outExt;
	const std::string       outPath;
	const std::string       outVideoFile;
	const std::string       start_ts;
	const Timestamp         tsStart;
	const SessionLogger_ptr pLogger;
	const bool              fRepromonEnabled;
	RepromonQueue*          pRepromonQueue;
	const bool              fTopLogFfmpeg;
	const std::string       duct_prefix;
};


using ExtProcThread = WorkerThread<ExtProcParams>;
using FfmpegThread = WorkerThread<FfmpegParams>;


class VideoCaptureApp: public CaptureApp {
private:
	SingleThreadExecutor<ExtProcThread> m_extProcExec;
	SingleThreadExecutor<FfmpegThread>  m_ffmpegExec;
	bool                                m_fTopLogFfmpeg;

	void checkExtProc(const std::string& mode);
	void onCaptureStartInternal(bool fRecovery	= false);

	void startRecording(int cx, int cy, const std::string& frameRate,
							   const std::string& v_dev, const std::string& a_dev,
							   bool fRecovery);
	void stopRecording(const std::string& start_ts,
					   const std::string& vpath,
					   const std::string& message);
public:
	VideoCaptureApp();
	~VideoCaptureApp();

	//
	void onCaptureIdle() override;
	void onCaptureStart() override;
	void onCaptureStop(const std::string& message) override;
	int  parseOpts(AppOpts& opts, int argc, char* argv[]) override;
};

#endif //CAPTURE_VIDEOCAPTURE_H
