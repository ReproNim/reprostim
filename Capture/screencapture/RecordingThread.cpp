#include <iostream>
#include <fstream>
#include <unistd.h>
#include <fcntl.h>
#include <filesystem>
#include <cstring>
#include <atomic>
#include <thread>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>
#include <opencv2/opencv.hpp>
#include "CaptureLib.h"
#include "RecordingThread.h"

using namespace reprostim;

////////////////////////////////////////////////////////////////////////

// TODO: work on algorithm to detect changes better
inline int calcFrameDiff(unsigned char *f1, unsigned char *f2, size_t len) {
	/*
	int diffSum = 0;
	for (size_t j = 0; j < len; j++) {
		int i1 = static_cast<int>(f1[j]);
		int i2 = static_cast<int>(f2[j]);
		//diffSum += abs(i1 - i2);
		if( i1 != i2 ) {
			diffSum++;
		}
	}
	_INFO("calcDiff: diffSum=" << diffSum);
	return diffSum;*/

	int difference = 0;
	for (size_t j = 0; j < len; j++) {
		difference += abs(static_cast<int>(f1[j]) - static_cast<int>(f2[j]));
	}
	//_INFO("calcDiff: difference=" << difference);
	return difference;
}

int recordScreens(const RecordingParams& rp, std::function<bool()> isTerminated) {
	_VERBOSE("recordScreens enter, sessionId=" << rp.sessionId);
	int fd = open(rp.videoDevPath.c_str(), O_RDWR);
	if (fd == -1) {
		_ERROR("Failed to open " << rp.videoDevPath);
		return -1;
	}

	// Query the device capabilities
	v4l2_capability cap;
	if (ioctl(fd, VIDIOC_QUERYCAP, &cap) == -1) {
		_ERROR("Failed to query device capabilities");
		close(fd);
		return -1;
	}

	// Set the format (e.g., YUYV)
	v4l2_format fmt;
	memset(&fmt, 0, sizeof(fmt));
	fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
	fmt.fmt.pix.width  = rp.cx; // 640;
	fmt.fmt.pix.height = rp.cy; // 480;
	if (ioctl(fd, VIDIOC_S_FMT, &fmt) == -1) {
		_ERROR("Failed to set v4l2 format: cx=" << rp.cx << ", cy=" << rp.cy);
		close(fd);
		return -1;
	}

	// Request buffers for memory mapping
	v4l2_requestbuffers reqbuf;
	memset(&reqbuf, 0, sizeof(reqbuf));
	reqbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	reqbuf.memory = V4L2_MEMORY_MMAP;
	reqbuf.count = 1; // number of buffers
	if (ioctl(fd, VIDIOC_REQBUFS, &reqbuf) == -1) {
		_ERROR("Failed to request buffers");
		close(fd);
		return -1;
	}

	// Map the buffer to user space
	v4l2_buffer buf;
	memset(&buf, 0, sizeof(buf));
	buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	buf.memory = V4L2_MEMORY_MMAP;
	buf.index = 0;
	if (ioctl(fd, VIDIOC_QUERYBUF, &buf) == -1) {
		_ERROR("Failed to query buffer");
		close(fd);
		return -1;
	}

	void* buffer = mmap(nullptr, buf.length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, buf.m.offset);
	if (buffer == MAP_FAILED) {
		_ERROR("Failed to map buffer");
		close(fd);
		return -1;
	}

	// Start capturing
	if (ioctl(fd, VIDIOC_STREAMON, &buf.type) == -1) {
		_ERROR("Failed to start capture");
		munmap(buffer, buf.length);
		close(fd);
		return -1;
	}

	// Variables to store two consecutive frames
	unsigned char* previousFrame = new unsigned char[buf.length];
	unsigned char* currentFrame = new unsigned char[buf.length];
	int nFrame = 0;
	bool fSave = false;
	long long nextSaveTime = currentTimeMs() + rp.intervalMs;

	//std::string start_ts = getTimeStr();
	std::filesystem::path sessionPath = std::filesystem::path(rp.outPath) / (rp.start_ts + "_");
	if( !std::filesystem::exists(sessionPath) ) {
		_INFO("Create session " << rp.sessionId << " directory: " << sessionPath.string());
		std::filesystem::create_directory(sessionPath);
	}

	_SESSION_LOG_BEGIN(rp.pLogger);

	// Capturing and comparing loop
	while (true) {
		if( isTerminated() ) {
			_INFO("Capture terminated for session " << rp.sessionId);
			break;
		}

		// Capture a frame, enqueue buffer
		if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
			_ERROR("Failed to capture frame (enqueue buffer)");
			break;
		}
		// Capture a frame, dequeue buffer
		if (ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
			_ERROR("Failed to capture frame (dequeue buffer)");
			break;
		}

		memcpy(currentFrame, buffer, buf.length);
		// Save the first frame
		if( nFrame==0 ) {
			memcpy(previousFrame, buffer, buf.length);
		}
		nFrame++;

		fSave = false;

		// always save first frame
		if( nFrame==1 ) {
			fSave = true;
			_VERBOSE("Save frame: first frame");
		}

		// save frame when difference is above threshold
		int difference = calcFrameDiff(currentFrame, previousFrame, buf.length);
		if (difference > rp.threshold  ) {
			fSave = true;
			_VERBOSE("Save frame: difference=" << difference);
		}

		// check obligatory save interval
		if( rp.intervalMs>0 && currentTimeMs() > nextSaveTime ) {
			fSave = true;
			_VERBOSE("Save frame: interval");
		}

		if (fSave) {
			nextSaveTime = currentTimeMs() + rp.intervalMs;

			std::string baseName = getTimeStr();
			std::filesystem::path basePath = sessionPath / baseName;

			if (rp.dumpRawFrame) {
				std::string rawPath = basePath.string() + ".bin";
				_INFO("Save frame [" << nFrame << "] to: " << rawPath);
				std::ofstream outputFile(rawPath, std::ios::binary);
				if (!outputFile.is_open()) {
					_ERROR("Error opening file for writing: " << rawPath);
					break;
				}

				outputFile.write(reinterpret_cast<char *>(currentFrame), buf.length);
				if (!outputFile.good()) {
					_ERROR("Error writing to file: " << rawPath);
					outputFile.close();
					break;
				}
				outputFile.close();
			}

			std::string pngPath = basePath.string() + ".png";
			//cv::Mat frame(cy, cx, CV_8UC3, currentFrame);
			cv::Mat yuyvImage(rp.cy, rp.cx, CV_8UC2, currentFrame);
			cv::Mat frame;
			cv::cvtColor(yuyvImage, frame, cv::COLOR_YUV2BGR_YUYV);
			_INFO("Save frame [" << nFrame << "] to: " << pngPath);
			cv::imwrite(pngPath, frame);
		}
		// Swap buffers for the next iteration
		unsigned char* temp = previousFrame;
		previousFrame = currentFrame;
		currentFrame = temp;
	}

	delete[] previousFrame;
	delete[] currentFrame;


	// Cleanup
	ioctl(fd, VIDIOC_STREAMOFF, &buf.type);
	munmap(buffer, buf.length);
	close(fd);

	std::string end_ts = getTimeStr();
	std::filesystem::path sessionPath2 = sessionPath;
	sessionPath2.replace_filename(rp.start_ts+"_"+end_ts);
	_INFO("Rename session " << rp.sessionId << " directory: "
		<< sessionPath.string() << " -> " << sessionPath2.string());
	std::filesystem::rename(sessionPath, sessionPath2);

	_VERBOSE("recordScreens leave, sessionId=" << rp.sessionId);
	_SESSION_LOG_END_CLOSE_RENAME(sessionPath2.string() + ".log");
	return 0;
}



////////////////////////////////////////////////////////////////////////

// specialization/override for default WorkerThread::run
template<>
void RecordingThread::run() {
	try {
		recordScreens(m_params,
					  [this]() { return isTerminated(); }
		);
	} catch(std::exception e) {
		_ERROR("Unhandled exception: " << e.what());
	};
}

