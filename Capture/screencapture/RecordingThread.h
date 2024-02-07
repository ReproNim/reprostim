#ifndef CAPTURE_RECORDINGTHREAD_H
#define CAPTURE_RECORDINGTHREAD_H

#include <iostream>
#include <atomic>
#include "CaptureThreading.h"

using namespace reprostim;

// Screen capture params shared between threads
// make sure it's thread-safe in usage
struct RecordingParams {
	bool verbose;
	int sessionId;
	int cx;
	int cy;
	int threshold;
	std::string outPath;
	std::string videoDevPath;
	bool dumpRawFrame;
	int intervalMs;
};

using RecordingThread = WorkerThread<RecordingParams>;

#endif //CAPTURE_RECORDINGTHREAD_H
