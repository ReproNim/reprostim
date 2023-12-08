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
#include "yaml-cpp/yaml.h"
#include "LibMWCapture/MWCapture.h"

// TODO: Consider moving this option to make file, e.g. CFLAGS += -Wno-write-strings
#pragma GCC diagnostic ignored "-Wwrite-strings"

using std::cerr;
using std::cout;
using std::endl;
namespace fs = std::filesystem;

/* ######################### begin common ############################# */

#ifndef _VERBOSE
#define _VERBOSE(expr) if( verbose ) { cout << expr << endl; }
#endif

#ifndef PATH_MAX_LEN
#define PATH_MAX_LEN 1024
#endif

std::string chiToString(MWCAP_CHANNEL_INFO& info) {
	std::stringstream s;
	s << "MWCAP_CHANNEL_INFO: faimilyID=" << info.wFamilyID;
	s << ", productID=" << info.wProductID;
	s << ", hardwareVersion=" << info.chHardwareVersion;
	s << ", firmwareID=" << static_cast<uint>(info.byFirmwareID);
	s << ", firmwareVersion=" << info.dwFirmwareVersion;
	s << ", familyName=" << info.szFamilyName;
	s << ", productName=" << info.szProductName;
	s << ", firmwareName=" << info.szFirmwareName;
	s << ", boardSerialNo=" << info.szBoardSerialNo;
	s << ", boardIndex=" << static_cast<uint>(info.byBoardIndex);
	s << ", channelIndex=" << static_cast<uint>(info.byChannelIndex);
	return s.str();
}

std::string exec(bool verbose, const std::string& cmd) {
	std::array<char, 128> buffer;
	std::string result;
	std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
	if (!pipe) {
		cerr << "popen() failed for cmd: " << cmd << endl;
		throw std::runtime_error("popen() failed!");
	}
	while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
		result += buffer.data();
	}
	_VERBOSE("exec -> :  " << result);
	return result;
}

std::vector<std::string> getVideoDevicePaths(const std::string& pattern) {
	glob_t glob_result;
	memset(&glob_result, 0, sizeof(glob_result));

	int return_value = glob(pattern.c_str(), GLOB_TILDE, NULL, &glob_result);
	if(return_value != 0) {
		globfree(&glob_result);
		std::stringstream ss;
		ss << "glob() failed with return_value " << return_value << endl;
		throw std::runtime_error(ss.str());
	}

	std::vector<std::string> filenames;
	for(size_t i = 0; i < glob_result.gl_pathc; ++i) {
		filenames.push_back(std::string(glob_result.gl_pathv[i]));
	}

	globfree(&glob_result);
	return filenames;
}

std::string getVideoDeviceSerial(bool verbose, const std::string& devPath) {
	std::string serialNumber;
	std::string cmd = "v4l2-ctl -d " + devPath + " --info";

	//std::string res = exec_cmd(verbose, cmd);
	std::string res = exec(verbose, cmd);
	//cout << "Result: " << res << endl;
	std::regex reVideoCapture("Video Capture");

	// Find "Device Caps" section
	std::size_t pos1 = res.find("Device Caps");
	if( pos1!=std::string::npos ) {
		res = res.substr(pos1);

		// Find "Video Capture" line in remaining text
		std::size_t pos2 = res.find("Video Capture");
		if( pos2!=std::string::npos ) {
			res = res.substr(pos2);

			// Find and parse "Serial : XXX" line in remaining text
			std::regex reSerial("Serial\\s+:\\s+(\\w+)");
			std::smatch mSerial;
			if (std::regex_search(res, mSerial, reSerial)) {
				// The serial number is in the first capture group (index 1)
				serialNumber = mSerial[1].str();
				_VERBOSE("Found Serial Number: " << serialNumber);
			}
		}
	}
	return serialNumber;
}

std::string getVideoDevicePathBySerial(bool verbose, const std::string& pattern, const std::string& serial) {
	std::string res;
	// NOTE: ?? should we use "v4l2-ctl --list-devices | grep /dev" to determine possible devices
	std::vector<std::string> v1 = getVideoDevicePaths(pattern);

	for (const auto& path : v1) {
		_VERBOSE(path);
		std::string sn = getVideoDeviceSerial(verbose, path);
		if( !sn.empty() && sn==serial ) {
			_VERBOSE("Found video device path: " << path << ", S/N=" << serial);
			res = path;
			break;
		}
	}
	return res;
}

std::string getTimeStr() {
	char mov[256] = {0};
	time_t now = time(0);
	tm *ltm = localtime(&now);
	int yr = 1900 + ltm->tm_year;
	int mo = 1 + ltm->tm_mon;
	int da = ltm->tm_mday;
	int hr = ltm->tm_hour;
	int mn = ltm->tm_min;
	int sc = ltm->tm_sec;
	sprintf(mov, "%d.%02d.%02d.%02d.%02d.%02d", yr, mo, da, hr, mn, sc);
	return mov;
}

void safeMWCloseChannel(HCHANNEL& hChannel) {
	if( hChannel != NULL) {
		MWCloseChannel(hChannel);
		hChannel = NULL;
	}
}

// Video signal status helpers
std::string vssFrameRate(const MWCAP_VIDEO_SIGNAL_STATUS& vss) {
	char frameRate[256] = {0};
	sprintf(frameRate, "%.0f", round( 10000000./(vss.dwFrameDuration==0?-1:vss.dwFrameDuration)));
	return frameRate;
}

bool vssEquals(const MWCAP_VIDEO_SIGNAL_STATUS& vss1,
			   const MWCAP_VIDEO_SIGNAL_STATUS& vss2) {
	// TODO: ?? structure has also x and y fields, but it isn't used in
	// original code, should we check it as well ??
	return
		( vss1.state           == vss2.state ) &&
		( vss1.cx              == vss2.cx ) &&
		( vss1.cy              == vss2.cy) &&
		( vss1.cxTotal         == vss2.cxTotal ) &&
		( vss1.cyTotal         == vss2.cyTotal ) &&
		( vss1.bInterlaced     == vss2.bInterlaced ) &&
		( vss1.dwFrameDuration == vss2.dwFrameDuration ) &&
		( vss1.nAspectX        == vss2.nAspectX ) &&
		( vss1.nAspectY        == vss2.nAspectY ) &&
		( vss1.bSegmentedFrame == vss2.bSegmentedFrame ) &&
		( vss1.frameType       == vss2.frameType ) &&
		( vss1.colorFormat     == vss2.colorFormat ) &&
		( vss1.quantRange      == vss2.quantRange ) &&
		( vss1.satRange        == vss2.satRange );
}

std::string vssToString(const MWCAP_VIDEO_SIGNAL_STATUS& vsStatus) {
	std::stringstream s;
	s << "MWCAP_VIDEO_SIGNAL_STATUS: state=" << vsStatus.state;
	s << ", x=" << vsStatus.x;
	s << ", y=" << vsStatus.y;
	s << ", cx=" << vsStatus.cx;
	s << ", cy=" << vsStatus.cy;
	s << ", cxTotal=" << vsStatus.cxTotal;
	s << ", cyTotal=" << vsStatus.cyTotal;
	s << ", bInterlaced=" << static_cast<bool>(vsStatus.bInterlaced);
	s << ", dwFrameDuration=" << vsStatus.dwFrameDuration;
	s << ", nAspectX=" << vsStatus.nAspectX;
	s << ", nAspectY=" << vsStatus.nAspectY;
	s << ", bSegmentedFrame=" << static_cast<bool>(vsStatus.bSegmentedFrame);
	s << ", frameType=" << vsStatus.frameType;
	s << ", colorFormat=" << vsStatus.colorFormat;
	s << ", quantRange=" << vsStatus.quantRange;
	s << ", satRange=" << vsStatus.satRange;
	return s.str();
}

/* ########################## end common ############################## */

/* ##################### begin options/config ######################### */

struct FfmpegOpts {
	std::string a_fmt;
	std::string a_nchan;
	std::string a_dev;
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
		cerr << "ERROR[008]: Failed load/parse config file "
		     << pathConfig << ": " << e.what() << endl;
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
		cerr << "ERROR[006]: Please provide valid options" << endl;
		cout << HELP_STR << endl;
		return 55;
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
				cout << HELP_STR << endl;
				return 1;
			case 'v':
				opts.verbose = true;
				break;
		}
	}

	// Terminate when REPROSTIM_HOME not specified
	if ( opts.homePath.empty() ){
		cerr << "ERROR[007]: REPROSTIM_HOME not specified, see -d" << endl;
		cout << HELP_STR << endl;
		return 55;
	}

	// Set config filename if not specified on input
	if ( opts.configPath.empty() ) {
		opts.configPath = opts.homePath + "/config.yaml";
	}

	// Set output directory if not specified on input
	if( opts.outPath.empty() ) {
		opts.outPath = opts.homePath + "/Videos";
	}
	return 0;
}

/* ###################### end options/config ########################## */

struct VideoDevice {
	std::string name;
	std::string serial;
	int         channelIndex = -1;
};

bool checkOutDir(bool verbose, const std::string& outDir) {
	if( !fs::exists(outDir)) {
		_VERBOSE("Output path not exists, creating...");
		if (fs::create_directories(outDir)) {
			_VERBOSE("Done.");
			return true;
		} else {
			_VERBOSE("Failed create output path: " << outDir);
			return false;
		}
	}
	return true;
}

bool findTargetVideoDevice(const AppConfig& cfg,
						   const AppOpts& opts,
						   VideoDevice& vd) {
	bool verbose = opts.verbose;
	vd.channelIndex = -1;
	MW_RESULT mwRes = MWRefreshDevice();
	if( mwRes!=MW_SUCCEEDED ) {
		cerr << "ERROR[004]: Failed MWRefreshDevice: " << mwRes << endl;
		return false;
	}
	int nCount = MWGetChannelCount();

	_VERBOSE("Channel count: " << nCount);

	if (nCount <= 0) {
		cout << "ERROR[001]: Can't find channels!" << endl;
		return false;
	}

	for (int i = 0; i < nCount; i++) {

		MWCAP_CHANNEL_INFO info;
		mwRes = MWGetChannelInfoByIndex(i, &info);

		_VERBOSE("Found device on channel " << i << ". " << chiToString(info));

		if (strcmp(info.szFamilyName, "USB Capture") == 0) {
			if( cfg.has_device_serial_number ) {
				if( cfg.device_serial_number==info.szBoardSerialNo ) {
					_VERBOSE("Found USB Capture device with S/N=" << info.szBoardSerialNo << " , index=" << i);
					vd.serial       = info.szBoardSerialNo;
					vd.name         = info.szProductName;
					vd.channelIndex = i;
					return true;
				} else {
					_VERBOSE("Unknown USB device with S/N=" << info.szBoardSerialNo << ", skip it, index=" << i);
				}
			} else {
				_VERBOSE("Found USB Capture device, index=" << i);
				vd.serial       = info.szBoardSerialNo;
				vd.name         = info.szProductName;
				vd.channelIndex = i;
				return true;
			}
		} else {
			if (info.wProductID == 0 && info.wFamilyID == 0) {
				cerr << "ERROR[003]: Access or permissions issue. Please check /etc/udev/rules.d/ configuration and docs." << endl;
				return false;
			} else {
				_VERBOSE("Unknown USB device, skip it, index=" << i);
			}
		}
	}
	return false;
}


std::string startRecording(
					const AppConfig& cfg,
					int cx, int cy,
					const std::string& frameRate,
					const std::string& outPath,
					const std::string& v_dev) {
	std::string start_ts = getTimeStr();
	char ffmpg[PATH_MAX_LEN] = {0};
	const FfmpegOpts& opts = cfg.ffm_opts;
	sprintf(
		ffmpg,
		"ffmpeg %s %s %s %s %s -framerate %s -video_size %ix%i %s -i %s "
		"%s %s %s %s %s/%s_.%s > /dev/null &",
		opts.a_fmt.c_str(),
		opts.a_nchan.c_str(),
		opts.a_opt.c_str(),
		opts.a_dev.c_str(),
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

	cout << start_ts;
	cout << ": <SYSTEMCALL> " << ffmpg << endl;
	system(ffmpg);
	return start_ts;
}

void stopRecording(const std::string& start_ts, const std::string& vpath) {
	std::string ffmpid;
	ffmpid = exec(true, "pidof ffmpeg");
	cout << "stop record says: " << ffmpid.c_str() << endl;
	while ( ffmpid.length() > 0 ) {
		cout << "<> PID of ffmpeg\t===> " << ffmpid.c_str() << endl;
		std::string stop_ts = getTimeStr();
		std::string killCmd = "kill -9 " + ffmpid;
		system(killCmd.c_str());
		//
		std::string oldname = vpath + "/" + start_ts + "_.mkv";
		std::string newname = vpath + "/" + start_ts + "_" + stop_ts + ".mkv";
		cout << stop_ts << ":\tKilling " << ffmpid.c_str() << ". Saving video ";
		cout << newname << endl;
		int x = 0;
		x = rename(oldname.c_str(), newname.c_str());
		usleep(1500000); // Allow time for ffmpeg to stop
		ffmpid = exec(true, "pidof ffmpeg");
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
		cout << stop_str << message << endl;
	}
}

std::string vdToString(VideoDevice& vd) {
	std::stringstream s;
	s << vd.name << ", S/N=" << vd.serial << ", channelIndex=" << vd.channelIndex;
	return s.str();
}


// Entry point
int main(int argc, char* argv[]) {
	AppOpts   opts;
	AppConfig cfg;

	const int res1 = parseOpts(opts, argc, argv);
	bool verbose = opts.verbose;

	if( res1==1 ) return 0; // help message
	if( res1!=0 ) return res1;

	_VERBOSE("Config file: " << opts.configPath);

	if( !loadConfig(cfg, opts.configPath) ) {
		// config.yaml load/parse problems
		return -8;
	}

	_VERBOSE("Output path: " << opts.outPath);
	if( !checkOutDir(verbose, opts.outPath) ) {
		// invalid output path
		cerr << "ERROR[009]: Failed create/locate output path: " << opts.outPath << endl;
		return -9;
	}

	// calculated options
	VideoDevice targetDev;
	std::string targetVideoDevPath;

	// current video signal status
	MWCAP_VIDEO_SIGNAL_STATUS vssCur = {};

	// previous video signal status
	MWCAP_VIDEO_SIGNAL_STATUS vssPrev = {};

	bool fRun = true;
	int recording = 0;
	std::string init_ts;
	std::string start_ts;
	std::string frameRate;

	MW_RESULT mr = MW_SUCCEEDED;

	init_ts = getTimeStr();
	cout << init_ts;
	cout << ": <><><> Starting VideoCapture <><><>" << endl;

	cout << "    <> Saving Videos to            ===> " << opts.outPath << endl;;
	cout << "    <> Recording from Video Device ===> ";
	cout << cfg.ffm_opts.v_dev;
	cout << ", S/N=" << (cfg.has_device_serial_number?cfg.device_serial_number:"auto");
	cout << endl;

	if( cfg.has_device_serial_number ) {
		_VERBOSE("Use device with specified S/N: " << cfg.device_serial_number);
	} else {
		_VERBOSE("Use any first available Magewell USB Capture device");
	}

	BOOL fInit = MWCaptureInitInstance();
	if( !fInit )
		cerr << "ERROR[005]: Failed MWCaptureInitInstance" << endl;

	do {
		usleep(1000000);
		HCHANNEL hChannel = NULL;
		if( !findTargetVideoDevice(cfg, opts, targetDev) ) {
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
				} else {
					targetVideoDevPath = getVideoDevicePathBySerial(opts.verbose,
																	cfg.video_device_path_pattern,
																	targetDev.serial);
					if( targetVideoDevPath.empty() ) {
						targetVideoDevPath = "/dev/video_not_found_911";
						cerr << "ERROR[007]: video device path not found by S/N: " << targetDev.serial
							 << ", use fallback one: " << targetVideoDevPath << endl;
					}
				}

				if( !cfg.ffm_opts.has_v_dev || !cfg.has_device_serial_number ) {
					cout << "    <> Found Video Device          ===> "
						 << targetVideoDevPath << ", S/N: " << targetDev.serial
						 << ", " << targetDev.name << endl;
				}

				start_ts = startRecording(cfg, vssCur.cx, vssCur.cy, frameRate,
										  opts.outPath, targetVideoDevPath);
				recording = 1;
				cout << start_ts << ":\tStarted Recording: " << endl;
				cout << "Apct Rat: " << vssCur.cx << "x" << vssCur.cy << endl;
				cout << "FR: " << frameRate << endl;
				usleep(5000000);
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
	} while ( fRun );

	safeStopRecording(opts, recording, start_ts, "Program terminated");

	if( fInit )
		MWCaptureExitInstance();
	return 0;
}