#include <iostream>
#include <fstream>
#include <unistd.h>
#include <fcntl.h>
#include <filesystem>
#include <linux/videodev2.h>
#include <opencv2/opencv.hpp>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <cstring>
#include <sysexits.h>
#include "ScreenCapture.h"

using namespace reprostim;

// TODO:
//  v4l2-ctl --stream-mmap --stream-count=1 --stream-to=file.png --device=/dev/video0
//  sudo apt-get update
//  sudo apt-get install libopencv-dev
//  g++ -o capture capture.cpp -std=c++17 -lopencv_core -lopencv_highgui -lopencv_imgcodecs

int recordScreens(bool verbose,
				int cx, int cy,
				int threshold,
				const std::string& outPath,
				const std::string& videoDevPath) {
	int fd = open(videoDevPath.c_str(), O_RDWR);
	if (fd == -1) {
		_ERROR("Failed to open " << videoDevPath);
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
	fmt.fmt.pix.width  = cx; // 640;
	fmt.fmt.pix.height = cy; // 480;
	if (ioctl(fd, VIDIOC_S_FMT, &fmt) == -1) {
		_ERROR("Failed to set format");
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

	// Capture a single frame (as an example)
	if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
		_ERROR("Failed to enqueue buffer");
		ioctl(fd, VIDIOC_STREAMOFF, &buf.type);
		munmap(buffer, buf.length);
		close(fd);
		return -1;
	}

	if (ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
		_ERROR("Failed to dequeue buffer");
		ioctl(fd, VIDIOC_STREAMOFF, &buf.type);
		munmap(buffer, buf.length);
		close(fd);
		return -1;
	}

	// At this point, the buffer contains the captured frame.
	// Variables to store two consecutive frames
	unsigned char* previousFrame = new unsigned char[buf.length];
	unsigned char* currentFrame = new unsigned char[buf.length];
	bool isFirstFrame = true;

	// Capturing and comparing loop
	for (int i = 0; i < 1000; i++) { // Capture 1000 frames as an example
		// Capture a frame
		if (ioctl(fd, VIDIOC_QBUF, &buf) == -1 || ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
			_ERROR("Failed to capture frame");
			break;
		}
		memcpy(isFirstFrame ? previousFrame : currentFrame, buffer, buf.length);

		// If it's not the first frame, compare it with the previous one
		if (!isFirstFrame) {
			int difference = 0;
			for (size_t j = 0; j < buf.length; j++) {
				difference += abs(static_cast<int>(currentFrame[j]) - static_cast<int>(previousFrame[j]));
			}

			if (difference > threshold) { // SOME_THRESHOLD) {
				// Print the current timestamp
				/*
				/// some abomination code from chatgpt since apparently no easy way for subsecs
				const auto now = std::chrono::system_clock::now();
				auto seconds = std::chrono::time_point_cast<std::chrono::seconds>(now);
				auto subseconds = now - seconds;
				auto milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(subseconds).count();
				std::time_t currentTime = std::time(nullptr);
				std::tm* localTime = std::localtime(&currentTime);
				*/
				std::string ts = getTimeStr();
				_VERBOSE(ts << " change " << difference << " detected");

				std::string frameName = ts + ".bin";
				std::filesystem::path path = std::filesystem::path(outPath) / frameName;
				std::string framePath = path.string();
				_INFO("Save to: " << framePath);
				std::ofstream outputFile(framePath, std::ios::binary);
				if (!outputFile.is_open()) {
					_ERROR("Error opening file for writing: " << framePath);
					return 1;
				}

				outputFile.write(reinterpret_cast<char*>(currentFrame), buf.length);
				if (!outputFile.good()) {
					_ERROR("Error writing to file: " << framePath);
					return 1;
				}

				outputFile.close();

				//cv::Mat frame(cy, cx, CV_8UC3, currentFrame);
				cv::Mat yuyvImage(cy, cx, CV_8UC2, currentFrame);
				cv::Mat frame;
				cv::cvtColor(yuyvImage, frame, cv::COLOR_YUV2BGR_YUYV);

				std::string framePath2 = framePath + ".png";
				cv::imwrite(framePath2, frame);
			}

			// Swap buffers for the next iteration
			unsigned char* temp = previousFrame;
			previousFrame = currentFrame;
			currentFrame = temp;
		} else {
			isFirstFrame = false;
		}
	}

	delete[] previousFrame;
	delete[] currentFrame;


	// Cleanup
	ioctl(fd, VIDIOC_STREAMOFF, &buf.type);
	munmap(buffer, buf.length);
	close(fd);

	return 0;
}

////////////////////////////////////////////////////////////////////////////
// ScreenCaptureApp class

ScreenCaptureApp::ScreenCaptureApp() {
	appName = "ScreenCapture";
	audioEnabled = false;
}

void ScreenCaptureApp::onCaptureStart() {
	_INFO("TODO: start snapshots");
	recording = 1;
	recordScreens(opts.verbose,
				  vssCur.cx, vssCur.cy,
				  30000,
				  opts.outPath,
				  targetVideoDevPath);
}

void ScreenCaptureApp::onCaptureStop(const std::string& message) {
	if( recording>0 ) {
		_INFO("TODO: stop snapshots. " << message);
		recording = 0;
	}
}

int ScreenCaptureApp::parseOpts(AppOpts& opts, int argc, char* argv[]) {
	const std::string HELP_STR = "Usage: reprostim-screencapture -d <path> [-o <path> | -h | -v ]\n\n"
								 "\t-d <path>\t$REPROSTIM_HOME directory (not optional)\n"
								 "\t-o <path>\tOutput directory where to save recordings (optional)\n"
								 "\t         \tDefaults to $REPROSTIM_HOME/Screens\n"
								 "\t-c <path>\tPath to configuration config.yaml file (optional)\n"
								 "\t         \tDefaults to $REPROSTIM_HOME/config.yaml\n"
								 "\t-v       \tVerbose, provides detailed information to stdout\n"
								 "\t-h       \tPrint this help string\n";

	int c = 0;
	if (argc == 1) {
		_ERROR("ERROR[006]: Please provide valid options");
		_INFO(HELP_STR);
		return EX_USAGE;
	}

	while( ( c = getopt (argc, argv, "d:o:c:hv") ) != -1 ) {
		switch(c) {
			case 'o':
				if(optarg) opts.outPath = optarg;
				break;
			case 'c':
				if(optarg) opts.configPath = optarg;
				break;
			case 'd':
				if(optarg) opts.homePath = optarg;
				break;
			case 'h':
				_INFO(HELP_STR);
				return 1;
			case 'v':
				opts.verbose = true;
				break;
		}
	}

	// Terminate when REPROSTIM_HOME not specified
	if ( opts.homePath.empty() ){
		_ERROR("ERROR[007]: REPROSTIM_HOME not specified, see -d");
		_INFO(HELP_STR);
		return EX_USAGE;
	}

	// Set config filename if not specified on input
	if ( opts.configPath.empty() ) {
		opts.configPath = opts.homePath + "/config.yaml";
	}

	// Set output directory if not specified on input
	if( opts.outPath.empty() ) {
		opts.outPath = opts.homePath + "/Screens";
	}
	return EX_OK;
}

