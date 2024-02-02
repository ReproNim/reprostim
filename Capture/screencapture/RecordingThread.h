#ifndef CAPTURE_RECORDINGTHREAD_H
#define CAPTURE_RECORDINGTHREAD_H

#include <iostream>
#include <atomic>

using namespace reprostim;

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


class RecordingThread {

private:
	const RecordingParams m_params;
	std::atomic<bool>     m_running;
	std::atomic<bool>     m_terminate;
	bool                  verbose;

	void run();

public:
	RecordingThread(const RecordingParams &params);

	virtual ~RecordingThread();

	bool isRunning() const;

	void start();

	void stop();
};

#endif //CAPTURE_RECORDINGTHREAD_H
