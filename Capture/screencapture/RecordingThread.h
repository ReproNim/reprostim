#ifndef CAPTURE_RECORDINGTHREAD_H
#define CAPTURE_RECORDINGTHREAD_H

#include <iostream>
#include <atomic>
#include "CaptureThreading.h"

using namespace reprostim;

// Screen capture params shared between threads
// make sure it's thread-safe in usage
struct RecordingParams {
	const bool verbose;
	const int sessionId;
	const int cx;
	const int cy;
	const int threshold;
	const std::string outPath;
	const std::string videoDevPath;
	const bool dumpRawFrame;
	const int intervalMs;
	const std::string& start_ts;
	const SessionLogger_ptr pLogger;
};

using RecordingThread = WorkerThread<RecordingParams>;

#endif //CAPTURE_RECORDINGTHREAD_H
