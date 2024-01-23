#include <iostream>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <unistd.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <cstring>
#include <sysexits.h>
#include "ScreenCapture.h"

using namespace reprostim;

int main1() {
    int fd = open("/dev/video4", O_RDWR);
    if (fd == -1) {
        perror("Failed to open /dev/video4");
        return -1;
    }

    // Query the device capabilities
    v4l2_capability cap;
    if (ioctl(fd, VIDIOC_QUERYCAP, &cap) == -1) {
        perror("Failed to query device capabilities");
        close(fd);
        return -1;
    }

    // Set the format (e.g., YUYV)
    v4l2_format fmt;
    memset(&fmt, 0, sizeof(fmt));
    fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
    fmt.fmt.pix.width = 640;
    fmt.fmt.pix.height = 480;
    if (ioctl(fd, VIDIOC_S_FMT, &fmt) == -1) {
        perror("Failed to set format");
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
        perror("Failed to request buffers");
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
        perror("Failed to query buffer");
        close(fd);
        return -1;
    }

    void* buffer = mmap(nullptr, buf.length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, buf.m.offset);
    if (buffer == MAP_FAILED) {
        perror("Failed to map buffer");
        close(fd);
        return -1;
    }

    // Start capturing
    if (ioctl(fd, VIDIOC_STREAMON, &buf.type) == -1) {
        perror("Failed to start capture");
        munmap(buffer, buf.length);
        close(fd);
        return -1;
    }

    // Capture a single frame (as an example)
    if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
        perror("Failed to enqueue buffer");
        ioctl(fd, VIDIOC_STREAMOFF, &buf.type);
        munmap(buffer, buf.length);
        close(fd);
        return -1;
    }

    if (ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
        perror("Failed to dequeue buffer");
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
    for (int i = 0; i < 1000; i++) { // Capture 100 frames as an example
        // Capture a frame
        if (ioctl(fd, VIDIOC_QBUF, &buf) == -1 || ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
            perror("Failed to capture frame");
            break;
        }
        memcpy(isFirstFrame ? previousFrame : currentFrame, buffer, buf.length);

        // If it's not the first frame, compare it with the previous one
        if (!isFirstFrame) {
            int difference = 0;
            for (size_t j = 0; j < buf.length; j++) {
                difference += abs(static_cast<int>(currentFrame[j]) - static_cast<int>(previousFrame[j]));
            }

            if (difference > 30000) { // SOME_THRESHOLD) {
                  // Print the current timestamp
                  /// some abomination code from chatgpt since apparently no easy way for subsecs
                  const auto now = std::chrono::system_clock::now();
                  auto seconds = std::chrono::time_point_cast<std::chrono::seconds>(now);
                  auto subseconds = now - seconds;
                  auto milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(subseconds).count();
                  std::time_t currentTime = std::time(nullptr);
                  std::tm* localTime = std::localtime(&currentTime);
                  std::cout << \
                    std::put_time(localTime, "%Y-%m-%d %H:%M:%S") <<  \
                    "." << milliseconds << \
                    " change " << difference << " detected!" << std::endl;
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
}

void ScreenCaptureApp::onCaptureStart() {
	_INFO("TODO: start snapshots");
	recording = 1;
	main1();
}

void ScreenCaptureApp::onCaptureStop(const std::string& message) {
	if( recording>0 ) {
		_INFO("TODO: stop snapshots. " << message);
		recording = 0;
	}
}

int ScreenCaptureApp::parseOpts(AppOpts& opts, int argc, char* argv[]) {
	const std::string HELP_STR = "Usage: ScreenCapture -d <path> [-o <path> | -h | -v ]\n\n"
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

