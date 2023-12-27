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
#include <chrono>
#include <thread>
#include <sysexits.h>
#include <alsa/asoundlib.h>
#include "yaml-cpp/yaml.h"
#include "LibMWCapture/MWCapture.h"

// TODO: Consider moving this option to make file, e.g. CFLAGS += -Wno-write-strings
#pragma GCC diagnostic ignored "-Wwrite-strings"

namespace fs = std::filesystem;

/* ######################### begin common ############################# */

#ifndef _ERROR
#define _ERROR(expr) std::cerr << expr << std::endl
#endif

#ifndef _INFO
#define _INFO(expr) std::cout << expr << std::endl
#endif

#ifndef _VERBOSE
#define _VERBOSE(expr) if( verbose ) { std::cout << expr << std::endl; }
#endif

#ifndef PATH_MAX_LEN
#define PATH_MAX_LEN 1024
#endif

#ifndef SLEEP_MS
#define SLEEP_MS(sec) std::this_thread::sleep_for(std::chrono::milliseconds(sec))
#endif

#ifndef SLEEP_SEC
#define SLEEP_SEC(sec) SLEEP_MS(static_cast<int>(sec*1000))
#endif


struct VDevSerial {
	std::string serialNumber;
	std::string busInfo;
};

struct VDevPath {
	std::string path;
	std::string busInfo;
};


std::string chiToString(MWCAP_CHANNEL_INFO& info) {
	std::ostringstream s;
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
		_ERROR("popen() failed for cmd: " << cmd);
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
		std::ostringstream ss;
		ss << "glob() failed with return_value " << return_value << std::endl;
		throw std::runtime_error(ss.str());
	}

	std::vector<std::string> filenames;
	for(size_t i = 0; i < glob_result.gl_pathc; ++i) {
		filenames.push_back(std::string(glob_result.gl_pathv[i]));
	}

	globfree(&glob_result);
	return filenames;
}

// NOTE: uses by-value result
VDevSerial getVideoDeviceSerial(bool verbose, const std::string& devPath) {
	VDevSerial vdi;
	std::string cmd = "v4l2-ctl -d " + devPath + " --info";

	//std::string res = exec_cmd(verbose, cmd);
	std::string res = exec(verbose, cmd);
	//_INFO("Result: " << res);
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
				vdi.serialNumber = mSerial[1].str();
				_VERBOSE("Found Serial Number: " << vdi.serialNumber);

				std::regex reBusInfo("Bus info\\s+:\\s+([\\w\\-\\:\\.]+)");
				std::smatch mBusInfo;
				if (std::regex_search(res, mBusInfo, reBusInfo)) {
					vdi.busInfo = mBusInfo[1].str();
					_VERBOSE("Found Bus Info: " << vdi.busInfo);
				}
			}
		}
	}
	return vdi;
}

// NOTE: uses by-value result
VDevPath getVideoDevicePathBySerial(bool verbose, const std::string& pattern, const std::string& serial) {
	VDevPath res;
	// NOTE: ?? should we use "v4l2-ctl --list-devices | grep /dev" to determine possible devices
	std::vector<std::string> v1 = getVideoDevicePaths(pattern);

	for (const auto& path : v1) {
		_VERBOSE(path);
		VDevSerial vdi = getVideoDeviceSerial(verbose, path);
		if( !vdi.serialNumber.empty() && vdi.serialNumber==serial ) {
			_VERBOSE("Found video device path: " << path << ", S/N=" << serial);
			res.path = path;
			res.busInfo = vdi.busInfo;
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

std::string mwcSdkVersion() {
	BYTE bMajor = 0;
	BYTE bMinor = 0;
	WORD wBuild = 0;

	if( MWGetVersion(&bMajor, &bMinor, &wBuild)==MW_SUCCEEDED ) {
		std::ostringstream ostm;
		ostm << int(bMajor) << "." << int(bMinor) << "." << int(wBuild);
		return ostm.str();
	}
	return "?.?.?";
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
	std::ostringstream s;
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

struct VideoDevice {
	std::string name;
	std::string serial;
	int         channelIndex = -1;
};

bool checkOutDir(bool verbose, const std::string& outDir) {
	if( !fs::exists(outDir)) {
		_VERBOSE("Output path not exists, creating...");
		if( fs::create_directories(outDir) ) {
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
		_ERROR("ERROR[004]: Failed MWRefreshDevice: " << mwRes);
		return false;
	}
	int nCount = MWGetChannelCount();

	_VERBOSE("Channel count: " << nCount);

	if (nCount <= 0) {
		_ERROR("ERROR[001]: Can't find channels!");
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
				_ERROR("ERROR[003]: Access or permissions issue. Please check /etc/udev/rules.d/ configuration and docs.");
				return false;
			} else {
				_VERBOSE("Unknown USB device, skip it, index=" << i);
			}
		}
	}
	return false;
}

std::string getAudioDevicePath(bool verbose, const std::string& busInfo) {
	std::string res;

	snd_ctl_t            *handle;
	snd_ctl_card_info_t  *info;
	// stack memory
	snd_ctl_card_info_alloca(&info);

	int card = -1;

	if (snd_card_next(&card) < 0 || card < 0) {
		return res;
	}

	_VERBOSE("Sound cards:");

	do {
		char card_name[32];
		sprintf(card_name, "hw:%d", card);

		if (snd_ctl_open(&handle, card_name, 0) < 0) {
			_VERBOSE("Cannot open control for card" << card);
			continue;
		}

		if( snd_ctl_card_info(handle, info) >= 0 )  {
			std::string id = snd_ctl_card_info_get_id(info);
			std::string name = snd_ctl_card_info_get_name(info);
			std::string lname = snd_ctl_card_info_get_longname(info);
			//_VERBOSE("Card " << int(card) << ": id=" << id << ", name=" << name << ", lname=" << lname);
			snd_ctl_close(handle);

			if( name.find("USB Capture")!=std::string::npos ) {
				if( !busInfo.empty() &&
					lname.find(busInfo)!=std::string::npos &&
					lname.find("Magewell")!=std::string::npos )
				{
					_VERBOSE("Found target audio card: " << card);
					std::ostringstream ostm;
					ostm << "hw:" << card << ",0";
					res = ostm.str();
					break;
				}
			}

		}
	} while (snd_card_next(&card) >= 0 && card >= 0);
	return res;
}

std::string startRecording(
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
		"%s %s %s %s %s/%s_.%s > /dev/null &",
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

	_INFO(start_ts << ": <SYSTEMCALL> " << ffmpg);
	system(ffmpg);
	return start_ts;
}

void stopRecording(const std::string& start_ts, const std::string& vpath) {
	std::string ffmpid;
	ffmpid = exec(true, "pidof ffmpeg");
	_INFO("stop record says: " << ffmpid.c_str());
	while ( ffmpid.length() > 0 ) {
		_INFO("<> PID of ffmpeg\t===> " << ffmpid.c_str());
		std::string stop_ts = getTimeStr();
		std::string killCmd = "kill -9 " + ffmpid;
		system(killCmd.c_str());
		//
		std::string oldname = vpath + "/" + start_ts + "_.mkv";
		std::string newname = vpath + "/" + start_ts + "_" + stop_ts + ".mkv";
		_INFO(stop_ts << ":\tKilling " << ffmpid.c_str() << ". Saving video " << newname);
		int x = 0;
		x = rename(oldname.c_str(), newname.c_str());
		SLEEP_SEC(1.5); // Allow time for ffmpeg to stop
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
		_INFO(stop_str << message);
	}
}

std::string vdToString(VideoDevice& vd) {
	std::ostringstream s;
	s << vd.name << ", S/N=" << vd.serial << ", channelIndex=" << vd.channelIndex;
	return s.str();
}

////////////////////////////////////////////////////////////////////////////
// Entry point
int main(int argc, char* argv[]) {
	AppOpts   opts;
	AppConfig cfg;

	const int res1 = parseOpts(opts, argc, argv);
	bool verbose = opts.verbose;

	if( res1==1 ) return EX_OK; // help message
	if( res1!=0 ) return res1;

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

	// calculated options
	VideoDevice targetDev;
	std::string targetBusInfo;
	std::string targetVideoDevPath;
	std::string targetAudioDevPath;

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

				start_ts = startRecording(cfg,
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
	} while ( fRun );

	safeStopRecording(opts, recording, start_ts, "Program terminated");

	if( fInit )
		MWCaptureExitInstance();
	return EX_OK;
}