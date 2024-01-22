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
#include <iomanip>
#include <sstream>
#include <filesystem>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <glob.h>
#include <fcntl.h>
#include <ctime>
#include <cmath>
#include <memory>
#include <stdexcept>
#include <string>
#include <regex>
#include <array>
#include <cstring>
#include <chrono>
#include <csignal>
#include <thread>
#include <sysexits.h>
#include <alsa/asoundlib.h>
#include "yaml-cpp/yaml.h"
#include "LibMWCapture/MWCapture.h"
#include "CaptureLib.h"

using namespace reprostim;

/* ##################### begin options/config ######################### */

struct FfmpegOpts {
	std::string a_fmt;
	std::string a_nchan;
	std::string a_dev;
	bool        has_a_dev = false;
	std::string a_opt;
	std::string v_fmt;
	std::string v_opt;
	std::string v_dev;
	bool        has_v_dev = false;
	std::string v_enc;
	std::string pix_fmt;
	std::string n_threads;
	std::string a_enc;
	std::string out_fmt;
};

// App configuration loaded from config.yaml, for
// historical reasons keep names in Python style
struct AppConfig {
	std::string device_serial_number;
	bool        has_device_serial_number = false;
	std::string video_device_path_pattern;
	FfmpegOpts  ffm_opts;
};

// App command-line options and args
struct AppOpts {
	std::string configPath;
	std::string homePath;
	std::string outPath;
	bool        verbose = false;
};

bool loadConfig(AppConfig& cfg, const std::string& pathConfig) {
	YAML::Node doc;
	try {
		doc = YAML::LoadFile(pathConfig);
	} catch(const std::exception& e) {
		_ERROR("ERROR[008]: Failed load/parse config file "
		     << pathConfig << ": " << e.what());
		return false;
	}

	if( doc["device_serial_number"] ) {
		cfg.device_serial_number = doc["device_serial_number"].as<std::string>();
		cfg.has_device_serial_number = !cfg.device_serial_number.empty() &&
		                               cfg.device_serial_number!="auto";
	} else {
		cfg.has_device_serial_number = false;
	}

	if( doc["video_device_path_pattern"] ) {
		cfg.video_device_path_pattern = doc["video_device_path_pattern"].as<std::string>();
	}

	if( doc["ffm_opts"] ) {
		YAML::Node node = doc["ffm_opts"];
		FfmpegOpts& opts = cfg.ffm_opts;
		opts.a_fmt = node["a_fmt"].as<std::string>();
		opts.a_nchan = node["a_nchan"].as<std::string>();
		opts.a_opt = node["a_opt"].as<std::string>();
		opts.a_dev = node["a_dev"].as<std::string>();
		opts.has_a_dev = !opts.a_dev.empty() && opts.a_dev != "auto";
		opts.v_fmt = node["v_fmt"].as<std::string>();
		opts.v_opt = node["v_opt"].as<std::string>();
		opts.v_dev = node["v_dev"].as<std::string>();
		opts.v_enc = node["v_enc"].as<std::string>();
		opts.has_v_dev = !opts.v_dev.empty() && opts.v_dev != "auto";
		opts.pix_fmt = node["pix_fmt"].as<std::string>();
		opts.n_threads = node["n_threads"].as<std::string>();
		opts.a_enc = node["a_enc"].as<std::string>();
		opts.out_fmt = node["out_fmt"].as<std::string>();
	}
	return true;
}

int parseOpts(AppOpts& opts, int argc, char* argv[]) {
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

/* ###################### end options/config ########################## */

void threadFuncFfmpeg(bool verbose, const std::string& cmd) {
	std::thread::id tid= std::this_thread::get_id();
	_VERBOSE("threadFuncFfmpeg start [" << tid << "]: " << cmd);
	exec(verbose, cmd, true);
	_VERBOSE("threadFuncFfmpeg leave [" << tid << "]: " << cmd);
}

std::string startRecording(
					bool verbose,
					const AppConfig& cfg,
					int cx, int cy,
					const std::string& frameRate,
					const std::string& outPath,
					const std::string& v_dev,
					const std::string& a_dev) {
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

void stopRecording(const std::string& start_ts, const std::string& vpath) {
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

void safeStopRecording(const AppOpts& opts,
					   int& recording,
					   const std::string& start_ts,
					   const std::string& message
					   ) {
	if ( recording > 0 ) {
		std::string stop_str = getTimeStr();
		stopRecording(start_ts, opts.outPath);
		recording = 0;
		_INFO(stop_str << message);
	}
}

void signalHandler(int signum) {
	//_INFO("Signal received: " << signum);
	if (signum == SIGINT) {
		_INFO("Ctrl+C received. Terminating...");
		if(isSysBreakExec() ) {
			_INFO("Force exit, 2nd attempt");
			std::exit(signum);
		}
		setSysBreakExec(true);
	}
	if( signum == SIGTERM  || signum == SIGKILL ) {
		_INFO("Termination or kill: " << signum);
		if(isSysBreakExec() ) {
			_INFO("Force exit, 2nd attempt");
			std::exit(signum);
		}
		setSysBreakExec(true);
	}
}

int appRun(int argc, char* argv[]) {
	AppOpts   opts;
	AppConfig cfg;

	std::signal(SIGINT,  signalHandler);
	std::signal(SIGTERM, signalHandler);
	std::signal(SIGKILL, signalHandler);


	const int res1 = parseOpts(opts, argc, argv);
	bool verbose = opts.verbose;

	if( res1==1 ) return EX_OK; // help message
	if( res1!=EX_OK ) return res1;

	_VERBOSE("Config file: " << opts.configPath);

	if( !loadConfig(cfg, opts.configPath) ) {
		// config.yaml load/parse problems
		return EX_CONFIG;
	}

	_VERBOSE("Output path: " << opts.outPath);
	if( !checkOutDir(verbose, opts.outPath) ) {
		// invalid output path
		_ERROR("ERROR[009]: Failed create/locate output path: " << opts.outPath);
		return EX_CANTCREAT;
	}

	const int res2 = checkSystem(verbose);
	if( res2!=EX_OK ) {
		// problem with system configuration and installed packages
		return res2;
	}

	// calculated options
	VideoDevice targetDev;
	std::string targetBusInfo;
	std::string targetVideoDevPath;
	std::string targetAudioDevPath;
	std::string configHash = getFileChangeHash(opts.configPath);

	// current video signal status
	MWCAP_VIDEO_SIGNAL_STATUS vssCur = {};

	// previous video signal status
	MWCAP_VIDEO_SIGNAL_STATUS vssPrev = {};

	bool fRun = true;
	bool fConfigChanged = false;
	int recording = 0;
	std::string init_ts;
	std::string start_ts;
	std::string frameRate;

	MW_RESULT mr = MW_SUCCEEDED;

	init_ts = getTimeStr();
	_INFO(init_ts << ": <><><> Starting VideoCapture <><><>");
	_INFO("    <> Saving Videos to            ===> " << opts.outPath);
	_INFO("    <> Recording from Video Device ===> " << cfg.ffm_opts.v_dev
		<< ", S/N=" << (cfg.has_device_serial_number?cfg.device_serial_number:"auto"));
	_INFO("    <> Recording from Audio Device ===> " << cfg.ffm_opts.a_dev);

	if( cfg.has_device_serial_number ) {
		_VERBOSE("Use device with specified S/N: " << cfg.device_serial_number);
	} else {
		_VERBOSE("Use any first available Magewell USB Capture device");
	}

	BOOL fInit = MWCaptureInitInstance();
	if( !fInit )
		_ERROR("ERROR[005]: Failed MWCaptureInitInstance");

	_VERBOSE("MWCapture SDK version: " << mwcSdkVersion());

	do {
		SLEEP_SEC(1);
		HCHANNEL hChannel = NULL;
		if( !findTargetVideoDevice(opts.verbose,
								   cfg.has_device_serial_number?cfg.device_serial_number:"",
								   targetDev) ) {
			safeStopRecording(opts, recording, start_ts, ":\tStopped recording. No channels!");
			_VERBOSE("Wait, no channels found");
			continue;
		}

		if( targetDev.channelIndex<0 ) {
			_VERBOSE("Wait, no valid USB devices found");
			continue;
		}

		_VERBOSE("Found target device: " << vdToString(targetDev));

		char wPath[256] = {0};
		mr = MWGetDevicePath(targetDev.channelIndex, wPath);
		_VERBOSE("Device path: " << wPath);

		// TODO: check res
		hChannel = MWOpenChannelByPath(wPath);

		// TODO: check res
		MWGetVideoSignalStatus(hChannel, &vssCur);

		frameRate = vssFrameRate(vssCur);

		// just dump current video signal status
		_VERBOSE(vssToString(vssCur) << ". frameRate=" << frameRate);

		if (  ( vssCur.cx > 0 ) && ( vssCur.cx  < 9999 ) && (vssCur.cy > 0) && (vssCur.cy < 9999)) {
			if (recording == 0) {
				// find target video device name/path when not specified explicitly
				if( cfg.ffm_opts.has_v_dev ) {
					targetVideoDevPath = cfg.ffm_opts.v_dev;
					targetBusInfo = "N/A";
				} else {
					VDevPath vdp = getVideoDevicePathBySerial(opts.verbose,
																	cfg.video_device_path_pattern,
																	targetDev.serial);
					targetVideoDevPath = vdp.path;
					targetBusInfo = vdp.busInfo;
					if( targetVideoDevPath.empty() ) {
						targetVideoDevPath = "/dev/video_not_found_911";
						_ERROR("ERROR[007]: video device path not found by S/N: " << targetDev.serial
							 << ", use fallback one: " << targetVideoDevPath);
					}
				}

				if( !cfg.ffm_opts.has_v_dev || !cfg.has_device_serial_number ) {
					_INFO("    <> Found Video Device          ===> "
						 << targetVideoDevPath << ", S/N: " << targetDev.serial
						 << ", busInfo: " << targetBusInfo
						 << ", " << targetDev.name);
				}

				if( cfg.ffm_opts.has_a_dev ) {
					targetAudioDevPath = cfg.ffm_opts.a_dev;
				} else {
					targetAudioDevPath = getAudioDevicePath(opts.verbose, targetBusInfo);
					_INFO("    <> Found Audio Device          ===> " << targetAudioDevPath);
				}
				_VERBOSE("Target ALSA audio device path: " << targetAudioDevPath);

				start_ts = startRecording(verbose,
				                          cfg,
										  vssCur.cx,
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
			else {
				if( !vssEquals(vssCur, vssPrev) ) {
					safeStopRecording(opts, recording, start_ts,
									  ":\tStopped recording because something changed.");
				}
			}
		}
		else {
			_VERBOSE("No valid video signal detected from target device");

			std::ostringstream message;
			message << ":\tWhack resolution: " << vssCur.cx << "x" << vssCur.cy;
			message << ". Stopped recording";
			safeStopRecording(opts, recording, start_ts, message.str());
		}

		vssPrev = vssCur;
		safeMWCloseChannel(hChannel);

		// check config changed
		std::string configHash2 = getFileChangeHash(opts.configPath);
		if( configHash!=configHash2 ) {
			_INFO("Config file was modified (" << configHash << " -> " << configHash2 << ") : " << opts.configPath);
			_INFO("Reloading config and restarting capture ...");
			fConfigChanged = true;
			fRun = false;
		}
	} while (fRun && !isSysBreakExec());

	safeStopRecording(opts, recording, start_ts, "Program terminated");

	if( fInit )
		MWCaptureExitInstance();

	if( isSysBreakExec() )
		return EX_SYS_BREAK_EXEC;

	if( fConfigChanged )
		return EX_CONFIG_RELOAD;

	return EX_OK;
}

////////////////////////////////////////////////////////////////////////////
// Entry point

int main(int argc, char* argv[]) {
	int res = EX_OK;
	do {
		res = appRun(argc, argv);
		optind = 0; // force restart argument scanning for getopt
	} while( res==EX_CONFIG_RELOAD );
	return res;
}
