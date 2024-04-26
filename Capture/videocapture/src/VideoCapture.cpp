/************************************************************************************************/
// VideoCapture.cpp : Detects if device connected or changes state, if video
// input available, then it calls ffmpeg to start recording video. If it changes
// state while recording it stops recording and begins a new recording if
// possible.
//
// This code is adapted and modified from the Magewell example code cited below.
// All licensing and legal matters pertaining thereunto are stipulated in the
// text below which has been preserved from the original Magewell distribution.
//
// Code bastardizer: Andy Connolly : andrew.c.connolly@dartmouth.edu date of
// bastardization inception: 01/15/2020
//
// <Original header begins after this line.>
//
// USBDeviceDetect.cpp : Defines the
// entry point for the console application.  MAGEWELL PROPRIETARY INFORMATION
// The following license only applies to head files and library within
// Magewell’s SDK and not to Magewell’s SDK as a whole.
//
// Copyrights © Nanjing Magewell Electronics Co., Ltd. (“Magewell”) All rights
// reserved.
//
// Magewell grands to any person who obtains the copy of Magewell’s head files
// and library the rights,including without limitation, to use, modify, publish,
// sublicense, distribute the Software on the conditions that all the following
// terms are met: - The above copyright notice shall be retained in any
// circumstances.  -The following disclaimer shall be included in the software
// and documentation and/or other materials provided for the purpose of publish,
// distribution or sublicense.
//
// THE SOFTWARE IS PROVIDED BY MAGEWELL “AS IS” AND ANY EXPRESS, INCLUDING BUT
// NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
// PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL MAGEWELL BE LIABLE
//
// FOR ANY CLAIM, DIRECT OR INDIRECT DAMAGES OR OTHER LIABILITY, WHETHER IN
// CONTRACT, TORT OR OTHERWISE, ARISING IN ANY WAY OF USING THE SOFTWARE.
//
// CONTACT INFORMATION:
// SDK@magewell.net
// http://www.magewell.com/
//
/************************************************************************************************/

#include <iostream>
#include <filesystem>
#include <stdio.h>
#include <unistd.h>
#include <memory>
#include <string>
#include <chrono>
#include <thread>
#include <sysexits.h>
#include <getopt.h>
#include "VideoCapture.h"

using namespace reprostim;

////////////////////////////////////////////////////////////////////////////
//

inline std::string buildVideoFile(
		const std::string& outPath,
		const std::string& name,
		const std::string& out_fmt) {
	return std::filesystem::path(outPath) / (name + "." + out_fmt);
}

std::string renameVideoFile(
		const std::string& outVideoFile,
		const std::string& outPath,
		const std::string& start_ts,
		const std::string& out_fmt,
		const std::string& message) {
	std::string stop_ts = getTimeStr();
	std::string outVideoFile2 = buildVideoFile(outPath, start_ts + "_" + stop_ts, out_fmt);
	if( std::filesystem::exists(outVideoFile) ) {
		_INFO(message << " Saving video " << outVideoFile2);
		rename(outVideoFile.c_str(), outVideoFile2.c_str());
	}
	return outVideoFile2;
}


// specialization/override for default WorkerThread::run
template<>
void FfmpegThread ::run() {
	_SESSION_LOG_BEGIN(getParams().pLogger);

	bool fRepromonEnabled = getParams().fRepromonEnabled;
	RepromonQueue* pRepromonQueue = getParams().pRepromonQueue;

	std::thread::id tid= std::this_thread::get_id();
	_VERBOSE("FfmpegThread start [" << tid << "]: " << getParams().cmd);

	_INFO(getParams().start_ts << ": <SYSTEMCALL> " << getParams().cmd);
	//system(cmd);

	// NOTE: in future improve async subprocess execution with reworked exec API.
	try {
		exec(getParams().cmd,
			 true, 48,
			 [this]() { return isTerminated(); }
		);
	} catch(std::exception& e) {
		_ERROR("FfmpegThread unhandled exception: " << e.what());
	}
	_VERBOSE("FfmpegThread terminating [" << tid << "]: " << getParams().cmd);

	std::string outVideoFile2 = renameVideoFile(getParams().outVideoFile,
					getParams().outPath,
					getParams().start_ts,
					getParams().outExt,
					":\tFfmpeg thread terminated.");

	// terminate session logs
	_VERBOSE("FfmpegThread leave [" << tid << "]: " << getParams().cmd);
	json jm = {
			{"type", "session_end"},
			{"ts", getTimeStr()},
			{"message", "ffmpeg thread terminated"},
			{"start_ts", getParams().start_ts}
	};
	_METADATA_LOG(jm);
	_SESSION_LOG_END_CLOSE_RENAME(outVideoFile2 + ".log");
	_NOTIFY_REPROMON(
		REPROMON_INFO,
		getParams().appName + " session " + getParams().start_ts +
		" end, saved to " + std::filesystem::path(outVideoFile2).filename().string()
	);
}

////////////////////////////////////////////////////////////////////////////
// VideoCaptureApp class

VideoCaptureApp::VideoCaptureApp() {
	appName = "reprostim-videocapture";
	audioEnabled = true;
}

VideoCaptureApp::~VideoCaptureApp() {
	m_ffmpegExec.shutdown();
}

void VideoCaptureApp::onCaptureStart() {
	startRecording(vssCur.cx,
				  vssCur.cy,
				  frameRate,
				  targetVideoDevPath,
				  targetAudioInDevPath);
	recording = 1;
	_INFO(start_ts << ":\tStarted Recording: ");
	_INFO("Apct Rat: " << vssCur.cx << "x" << vssCur.cy);
	_INFO("FR: " << frameRate);
	SLEEP_SEC(5);
}

void VideoCaptureApp::onCaptureStop(const std::string& message) {
	//_INFO("onCaptureStop");
	if ( recording > 0 ) {
		Timestamp tsStop = CURRENT_TIMESTAMP();
		std::string stop_ts = getTimeStr(tsStop);

		json jm = {
				{"type", "capture_stop"},
				{"ts", getTimeStr()},
				{"message", message},
				{"start_ts", start_ts},
				{"stop_ts", stop_ts}
		};
		_METADATA_LOG(jm);

		stopRecording(start_ts, outPath, message);
		recording = 0;
		_INFO(stop_ts << " " << message);
	}
}

int VideoCaptureApp::parseOpts(AppOpts& opts, int argc, char* argv[]) {
	const std::string HELP_STR = "Usage: reprostim-videocapture -d <path> [-o <path> | -h | -v ]\n\n"
								 "\t-d <path>\t$REPROSTIM_HOME directory (not optional)\n"
								 "\t-o <path>\tOutput directory where to save recordings (optional)\n"
								 "\t         \tDefaults to $REPROSTIM_HOME/Videos/{year}/{month}\n"
								 "\t-c <path>\tPath to configuration config.yaml file (optional)\n"
								 "\t         \tDefaults to $REPROSTIM_HOME/config.yaml\n"
								 "\t-v, --verbose\n"
								 "\t         \tVerbose, provides detailed information to stdout\n"
								 "\t-V, --version\n"
								 "\t         \tPrint version information\n"
								 "\t-l, --list-devices\n"
								 "\t         \tList devices, only audio is supported\n"
								 "\t-h, --help\n"
								 "\t         \tPrint this help string\n";

	int c = 0;
	if (argc == 1) {
		_ERROR("ERROR[006]: Please provide valid options");
		_INFO(HELP_STR);
		return EX_USAGE;
	}

	struct option longOpts[] = {
			{"help", no_argument, nullptr, 'h'},
			{"verbose", no_argument, nullptr, 'v'},
			{"version", no_argument, nullptr, 'V'},
			{"list-devices", no_argument, nullptr, 'l'},
			{nullptr, 0, nullptr, 0}
	};

	while ((c = getopt_long(argc, argv, "o:c:d:hvVl", longOpts, nullptr)) != -1) {
		switch(c) {
			case 'o':
				if(optarg) opts.outPathTempl = optarg;
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
			case 'l':
				listDevices();
				return 1;
			case 'v':
				opts.verbose = true;
				break;
			case 'V':
				printVersion();
				return 1;
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
	if( opts.outPathTempl.empty() ) {
		opts.outPathTempl = opts.homePath + "/Videos/{year}/{month}";
	}
	return EX_OK;
}

void VideoCaptureApp::startRecording(int cx, int cy, const std::string& frameRate,
		const std::string& v_dev, const std::string& a_dev) {
	tsStart = CURRENT_TIMESTAMP();
	start_ts = getTimeStr(tsStart);
	outPath = createOutPath();
	_INFO("    <> Current output path         ===> " << outPath);

	char ffmpg[PATH_MAX_LEN] = {0};
	const FfmpegOpts& opts = cfg.ffm_opts;
	std::string a_dev2 = a_dev;
	if( a_dev2.find("-i ")!=0 ) a_dev2 = "-i " + a_dev2;
	std::string outVideoFile = buildVideoFile(outPath, start_ts + "_", opts.out_fmt);
	sprintf(
			ffmpg,
			"ffmpeg %s %s %s %s %s -framerate %s -video_size %ix%i %s -i %s "
			"%s %s %s %s %s 2>&1", // > /dev/null &",
			opts.a_fmt.c_str(),
			opts.a_nchan.c_str(),
			opts.a_opt.c_str(),
			a_dev2.c_str(),
			opts.v_fmt.c_str(),
			frameRate.c_str(),
			cx,
			cy,
			opts.v_opt.c_str(),
			v_dev.c_str(),
			opts.v_enc.c_str(),
			opts.pix_fmt.c_str(),
			opts.n_threads.c_str(),
			opts.a_enc.c_str(),
			outVideoFile.c_str()
	);

	SessionLogger_ptr pLogger = createSessionLogger("session_logger_" + start_ts, outVideoFile + ".log");
	_SESSION_LOG_BEGIN(pLogger);
	json jm = {
			{"type", "session_begin"},
			{"ts", getTimeStr()},
			{"version", CAPTURE_VERSION_STRING},
			{"appName", appName},
			{"serial", targetVideoDev.serial},
			{"vDev", targetVideoDev.name},
			{"aDev", targetAudioInDev.alsaDeviceName},
			{"start_ts", start_ts},
			{"cx", cx},
			{"cy", cy},
			{"frameRate", frameRate}
	};
	_METADATA_LOG(jm);
	_NOTIFY_REPROMON(
		REPROMON_INFO,
		appName + " session " + start_ts + " begin, " +
		std::to_string(vssCur.cx) + "x" + std::to_string(vssCur.cy) + ", " + frameRate + " fps",
		{
			{"serial", targetVideoDev.serial},
			{"vDev", targetVideoDev.name},
			{"start_ts", start_ts},
			{"cx", vssCur.cx},
			{"cy", vssCur.cy},
			{"frameRate", frameRate}
		}
	);
	_VERBOSE("Created session logger: session_logger_" << start_ts);
	FfmpegThread* pt = FfmpegThread::newInstance(FfmpegParams{
			appName,
			ffmpg,
			opts.out_fmt,
			outPath,
			outVideoFile,
			start_ts,
			pLogger,
			fRepromonEnabled,
			pRepromonQueue.get() // NOTE: unsafe ownership
	});

	m_ffmpegExec.schedule(pt);
}

void VideoCaptureApp::stopRecording(const std::string& start_ts,
									const std::string& vpath,
									const std::string& message) {
	std::string out_fmt = cfg.ffm_opts.out_fmt;
	std::string oldname = buildVideoFile(vpath, start_ts + "_", out_fmt);
	std::string ffmpid = exec("pidof ffmpeg");
	_INFO("stop record says: " << ffmpid.c_str());
	while ( ffmpid.length() > 0 ) {
		_INFO("<> PID of ffmpeg\t===> " << ffmpid.c_str());
		std::string killCmd = "kill -9 " + ffmpid;
		system(killCmd.c_str());
		//
		SLEEP_SEC(1.5); // Allow time for ffmpeg to stop
		ffmpid = exec("pidof ffmpeg");
	}

	_SESSION_LOG_END();
	m_ffmpegExec.schedule(nullptr);

	// finally double check file again, as sometime ffmpeg
	// process killed while unfinished video file exists
	renameVideoFile(oldname, vpath, start_ts, out_fmt,
					":\tFound still unfinished video file, fixing it.");
}


