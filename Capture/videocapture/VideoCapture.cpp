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
#include "VideoCapture.h"

using namespace reprostim;

////////////////////////////////////////////////////////////////////////////
//

void threadFuncFfmpeg(bool verbose, const std::string& cmd) {
	std::thread::id tid= std::this_thread::get_id();
	_VERBOSE("threadFuncFfmpeg start [" << tid << "]: " << cmd);
	exec(verbose, cmd, true);
	_VERBOSE("threadFuncFfmpeg leave [" << tid << "]: " << cmd);
}

////////////////////////////////////////////////////////////////////////////
// VideoCaptureApp class

VideoCaptureApp::VideoCaptureApp() {
	appName = "VideoCapture";
}

void VideoCaptureApp::onCaptureStart() {
	start_ts = startRecording(vssCur.cx,
							  vssCur.cy,
							  frameRate,
							  opts.outPath,
							  targetVideoDevPath,
							  targetAudioDevPath);
	recording = 1;
	_INFO(start_ts << ":\tStarted Recording: ");
	_INFO("Apct Rat: " << vssCur.cx << "x" << vssCur.cy);
	_INFO("FR: " << frameRate);
	SLEEP_SEC(5);
}

void VideoCaptureApp::onCaptureStop(const std::string& message) {
	if ( recording > 0 ) {
		std::string stop_str = getTimeStr();
		stopRecording(start_ts, opts.outPath);
		recording = 0;
		_INFO(stop_str << message);
	}
}

int VideoCaptureApp::parseOpts(AppOpts& opts, int argc, char* argv[]) {
	const std::string HELP_STR = "Usage: VideoCapture -d <path> [-o <path> | -h | -v ]\n\n"
								 "\t-d <path>\t$REPROSTIM_HOME directory (not optional)\n"
								 "\t-o <path>\tOutput directory where to save recordings (optional)\n"
								 "\t         \tDefaults to $REPROSTIM_HOME/Videos\n"
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
		opts.outPath = opts.homePath + "/Videos";
	}
	return EX_OK;
}

std::string VideoCaptureApp::startRecording(int cx, int cy, const std::string& frameRate,
		const std::string& outPath, const std::string& v_dev, const std::string& a_dev) {
	std::string start_ts = getTimeStr();
	char ffmpg[PATH_MAX_LEN] = {0};
	const FfmpegOpts& opts = cfg.ffm_opts;
	std::string a_dev2 = a_dev;
	if( a_dev2.find("-i ")!=0 ) a_dev2 = "-i " + a_dev2;
	sprintf(
			ffmpg,
			"ffmpeg %s %s %s %s %s -framerate %s -video_size %ix%i %s -i %s "
			"%s %s %s %s %s/%s_.%s 2>&1", // > /dev/null &",
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
			outPath.c_str(),
			start_ts.c_str(),
			opts.out_fmt.c_str()
	);

	std::string cmd = ffmpg;
	_INFO(start_ts << ": <SYSTEMCALL> " << cmd.c_str());
	//system(cmd);
	std::thread t(&threadFuncFfmpeg, verbose, cmd);
	_VERBOSE("started recording thread: " << t.get_id());
	t.detach(); // make daemon thread
	return start_ts;
}

void VideoCaptureApp::stopRecording(const std::string& start_ts, const std::string& vpath) {
	std::string oldname = vpath + "/" + start_ts + "_.mkv";
	std::string ffmpid;
	ffmpid = exec(true, "pidof ffmpeg");
	_INFO("stop record says: " << ffmpid.c_str());
	while ( ffmpid.length() > 0 ) {
		_INFO("<> PID of ffmpeg\t===> " << ffmpid.c_str());
		std::string stop_ts = getTimeStr();
		std::string killCmd = "kill -9 " + ffmpid;
		system(killCmd.c_str());
		//
		std::string newname = vpath + "/" + start_ts + "_" + stop_ts + ".mkv";
		_INFO(stop_ts << ":\tKilling " << ffmpid.c_str() << ". Saving video " << newname);
		rename(oldname.c_str(), newname.c_str());
		SLEEP_SEC(1.5); // Allow time for ffmpeg to stop
		ffmpid = exec(true, "pidof ffmpeg");
	}

	// finally double check file again, as sometime ffmpeg
	// process killed while unfinished video file exists
	if( std::filesystem::exists(oldname) ) {
		std::string stop_ts = getTimeStr();
		std::string newname2 = vpath + "/" + start_ts + "_" + stop_ts + ".mkv";
		_INFO(":\tFound still unfinished video file, fixing it. Saving video " << newname2);
		rename(oldname.c_str(), newname2.c_str());
	}
}

