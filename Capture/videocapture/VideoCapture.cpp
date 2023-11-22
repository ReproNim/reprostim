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

/* ######################### begin common ############################# */

std::string exec(bool verbose, const char* cmd) {
	std::array<char, 128> buffer;
	std::string result;
	std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
	if (!pipe) {
		cerr << "popen() failed for cmd: " << cmd << endl;
		throw std::runtime_error("popen() failed!");
	}
	while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
		result += buffer.data();
	}
	if( verbose ) cout << "exec -> :  " << result << endl;
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
	char cmd[1024] = {0};
	sprintf(cmd, "v4l2-ctl -d %s --info", devPath.c_str());

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
				if( verbose ) std::cout << "Found Serial Number: " << serialNumber << std::endl;
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
		if( verbose ) cout << path << endl;
		std::string sn = getVideoDeviceSerial(verbose, path);
		if( !sn.empty() && sn==serial ) {
			if( verbose ) cout << "Found video device path: " << path << ", S/N=" << serial << endl;
			res = path;
			break;
		}
	}
	return res;
}

void getTimeStr(char mov[256]) {
	time_t now = time(0);
	tm *ltm = localtime(&now);
	int yr = 1900 + ltm->tm_year;
	int mo = 1 + ltm->tm_mon;
	int da = ltm->tm_mday;
	int hr = ltm->tm_hour;
	int mn = ltm->tm_min;
	int sc = ltm->tm_sec;
	sprintf(mov, "%d.%02d.%02d.%02d.%02d.%02d", yr, mo, da, hr, mn, sc);
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

void loadConfig(AppConfig& cfg, const std::string& pathConfig) {
	YAML::Node doc = YAML::LoadFile(pathConfig);

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
}

int parseOpts(AppOpts& opts, int argc, char* argv[]) {
	const char* HELP_STR = "Usage: VideoCapture -d <path> [-o <path> | -h | -v ]\n\n"
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
	if ( opts.configPath.empty() ){
		char c_fn[256];
		sprintf(c_fn, "%s/config.yaml", opts.homePath.c_str());
		opts.configPath = c_fn;
	}

	// Set output directory if not specified on input
	if( opts.outPath.empty() ) {
		opts.outPath = opts.homePath + "/Videos";
	}
	return 0;
}

/* ###################### end options/config ########################## */


void startRecording(const AppConfig& cfg, int cx, int cy, char fr[256],
					char starttime[256],
					const std::string& outPath,
					const std::string& v_dev) {
	getTimeStr(starttime);
	char ffmpg[1024] = {0};
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
		fr,
		cx,
		cy,
		opts.v_opt.c_str(),
		v_dev.c_str(),
		opts.v_enc.c_str(),
		opts.pix_fmt.c_str(),
		opts.n_threads.c_str(),
		opts.a_enc.c_str(),
		outPath.c_str(),
		starttime,
		opts.out_fmt.c_str()
	);

	cout << starttime;
	cout << ": <SYSTEMCALL> " << ffmpg << endl;
	system(ffmpg);
}

static void stopRecording(char start_str[256], const std::string& vpath) {
	std::string ffmpid;
	ffmpid = exec(true, "pidof ffmpeg");
	cout << "stop record says: " << ffmpid.c_str() << endl;
	while ( ffmpid.length() > 0 ) {
		cout << "<> PID of ffmpeg\t===> " << ffmpid.c_str() << endl;
		char stop_str[256] = {0};
		getTimeStr(stop_str);
		char killCmd[256] = {0};
		sprintf(killCmd, "kill -9 %s", ffmpid.c_str());
		system(killCmd);
		char oldname[256] = {0};
		char newname[512] = {0};
		sprintf(oldname, "%s/%s_.mkv", vpath.c_str(), start_str);
		sprintf(newname, "%s/%s_%s.mkv", vpath.c_str(), start_str, stop_str);
		cout << stop_str << ":\tKilling " << ffmpid.c_str() << ". Saving video ";
		cout << newname << endl;
		int x = 0;
		x = rename(oldname, newname);
		usleep(1500000); // Allow time for ffmpeg to stop
		ffmpid = exec(true, "pidof ffmpeg");
	}
}

// Entry point
int main(int argc, char* argv[]) {
	AppOpts   opts;
	AppConfig cfg;

	const int nOpts = parseOpts(opts, argc, argv);

	if( nOpts==1 ) return 0; // help message
	if( nOpts!=0 ) return nOpts;

	if( opts.verbose ) {
		cout << "Config file: " << opts.configPath << endl;
	}

	loadConfig(cfg, opts.configPath);

	if ( opts.verbose ) {
		cout << "Output path: " << opts.outPath << endl;
	}

	// calculated options
	std::string targetDevName;
	std::string targetDevSerial;
	std::string targetVideoDevPath;
	int         targetChannelIndex = -1;

	MWCAP_VIDEO_SIGNAL_STATE state;
	int cx = 0;
	int cy = 0;
	int cxTotal = 0;
	int cyTotal = 0;
	BOOLEAN bInterlaced = false;
	DWORD dwFrameDuration = 0;
	int nAspectX = 0;
	int nAspectY = 0;
	BOOLEAN bSegmentedFrame = false;
	MWCAP_VIDEO_FRAME_TYPE frameType;
	MWCAP_VIDEO_COLOR_FORMAT colorFormat;
	MWCAP_VIDEO_QUANTIZATION_RANGE quantRange;
	MWCAP_VIDEO_SATURATION_RANGE satRange;

	MWCAP_VIDEO_SIGNAL_STATE prev_state;
	int prev_cx = 0;
	int prev_cy = 0;
	int prev_cxTotal = 0;
	int prev_cyTotal = 0;
	BOOLEAN prev_bInterlaced = false;
	DWORD prev_dwFrameDuration = 0;
	int prev_nAspectX = 0;
	int prev_nAspectY = 0;
	BOOLEAN prev_bSegmentedFrame = false;
	MWCAP_VIDEO_FRAME_TYPE prev_frameType;
	MWCAP_VIDEO_COLOR_FORMAT prev_colorFormat;
	MWCAP_VIDEO_QUANTIZATION_RANGE prev_quantRange;
	MWCAP_VIDEO_SATURATION_RANGE prev_satRange;

	int recording = 0;
	char init_time[256] = {0};
	char start_str[256] = {0};
	char stop_str[256] = {0};
	int nMov = 0;
	char frameRate[256] = {0};

	MW_RESULT mr = MW_SUCCEEDED;

	getTimeStr(init_time);
	cout << init_time;
	cout << ": <><><> Starting VideoCapture <><><>" << endl;

	cout << "    <> Saving Videos to            ===> " << opts.outPath << endl;;
	cout << "    <> Recording from Video Device ===> ";
	cout << cfg.ffm_opts.v_dev;
	cout << ", S/N=" << (cfg.has_device_serial_number?cfg.device_serial_number:"auto");
	cout << endl;

	if( opts.verbose ) {
		if( cfg.has_device_serial_number )
			cout << "Use device with specified S/N: " << cfg.device_serial_number << endl;
		else
			cout << "Use any first available Magewell USB Capture device" << endl;
	}

	BOOL fInit = MWCaptureInitInstance();
	if( !fInit )
		cerr << "ERROR[005]: Failed MWCaptureInitInstance" << endl;

	do {
		usleep(1000000);
		HCHANNEL hChannel = NULL;
		MW_RESULT mwRes = MWRefreshDevice();
		if( mwRes!=MW_SUCCEEDED )
			cerr << "ERROR[004]: Failed MWRefreshDevice: " << mwRes << endl;
		int nCount = MWGetChannelCount();

		if( opts.verbose )
			cout << "Channel count: " << nCount << endl;

		if (nCount <= 0) {
			cout << "ERROR[001]: Can't find channels!" << endl;
			if ( recording > 0 ){
				getTimeStr(stop_str);
				stopRecording(start_str, opts.outPath);
				recording = 0;
				cout << stop_str << ":\tStopped recording. No channels!"<<endl;
				nMov++;
			}
			continue;
		}

		for (int i = 0; i < nCount; i++) {

			MWCAP_CHANNEL_INFO info;
			mr = MWGetChannelInfoByIndex(i, &info);

			if( opts.verbose ) {
				cout << "Found device on channel " << i;
				cout << ". MWCAP_CHANNEL_INFO: faimilyID=" << info.wFamilyID;
				cout << ", productID=" << info.wProductID;
				cout << ", hardwareVersion=" << info.chHardwareVersion;
				cout << ", firmwareID=" << static_cast<uint>(info.byFirmwareID);
				cout << ", firmwareVersion=" << info.dwFirmwareVersion;
				cout << ", familyName=" << info.szFamilyName;
				cout << ", productName=" << info.szProductName;
				cout << ", firmwareName=" << info.szFirmwareName;
				cout << ", boardSerialNo=" << info.szBoardSerialNo;
				cout << ", boardIndex=" << static_cast<uint>(info.byBoardIndex);
				cout << ", channelIndex=" << static_cast<uint>(info.byChannelIndex) << endl;
			}

			if (strcmp(info.szFamilyName, "USB Capture") == 0) {
				if( cfg.has_device_serial_number ) {
					if( cfg.device_serial_number==info.szBoardSerialNo ) {
						if( opts.verbose ) {
							cout << "Found USB Capture device with S/N="
								 << info.szBoardSerialNo << " , index=" << i << endl;
						}
						targetDevSerial = info.szBoardSerialNo;
						targetDevName = info.szProductName;
						targetChannelIndex = i;
						break;
					} else {
						if( opts.verbose ) {
							cout << "Unknown USB device with S/N=" << info.szBoardSerialNo
								 << ", skip it, index=" << i << endl;
						}
					}
				} else {
					if( opts.verbose ) {
						cout << "Found USB Capture device, index=" << i << endl;
					}
					targetDevSerial = info.szBoardSerialNo;
					targetDevName = info.szProductName;
					targetChannelIndex = i;
					break;
				}
			} else {
				if (info.wProductID == 0 && info.wFamilyID == 0) {
					cerr << "ERROR[003]: Access or permissions issue. Please check /etc/udev/rules.d/ configuration and docs." << endl;
					if (recording > 0) {
						getTimeStr(stop_str);
						stopRecording(start_str, opts.outPath);
						recording = 0;
						cout << stop_str << ":\tStopped recording. No channels!" << endl;
						nMov++;
					}
					//return -56; // NOTE: break or continue execution?
				} else {
					if( opts.verbose ) {
						cout << "Unknown USB device, skip it, index=" << i << endl;
					}
				}
			}
		}

		if( targetChannelIndex<0 ) {
			if( opts.verbose ) cout << "Wait, no valid USB devices found" << endl;
			continue;
		}

		char wPath[256] = {0};
		mr = MWGetDevicePath(targetChannelIndex, wPath);
		if( opts.verbose )
			cout << "Device path: " << wPath << endl;

		hChannel = MWOpenChannelByPath(wPath);
		MWCAP_VIDEO_SIGNAL_STATUS vsStatus;
		MWGetVideoSignalStatus(hChannel, &vsStatus);
		state           = vsStatus.state;
		cx              = vsStatus.cx;
		cy              = vsStatus.cy;
		cxTotal         = vsStatus.cxTotal;
		cyTotal         = vsStatus.cyTotal;
		bInterlaced     = vsStatus.bInterlaced;
		dwFrameDuration = vsStatus.dwFrameDuration;
		nAspectX        = vsStatus.nAspectX;
		nAspectY        = vsStatus.nAspectY;
		bSegmentedFrame = vsStatus.bSegmentedFrame;
		frameType       = vsStatus.frameType;
		colorFormat     = vsStatus.colorFormat;
		quantRange      = vsStatus.quantRange;
		satRange        = vsStatus.satRange;

		sprintf(frameRate, "%.0f", round( 10000000./(dwFrameDuration==0?-1:dwFrameDuration)));

		if( opts.verbose ) {
			cout << "MWCAP_VIDEO_SIGNAL_STATUS: state=" << vsStatus.state;
			cout << ", x=" << vsStatus.x;
			cout << ", y=" << vsStatus.y;
			cout << ", cx=" << vsStatus.cx;
			cout << ", cy=" << vsStatus.cy;
			cout << ", cxTotal=" << vsStatus.cxTotal;
			cout << ", cyTotal=" << vsStatus.cyTotal;
			cout << ", bInterlaced=" << static_cast<bool>(vsStatus.bInterlaced);
			cout << ", dwFrameDuration=" << vsStatus.dwFrameDuration;
			cout << ", nAspectX=" << vsStatus.nAspectX;
			cout << ", nAspectY=" << vsStatus.nAspectY;
			cout << ", bSegmentedFrame=" << static_cast<bool>(vsStatus.bSegmentedFrame);
			cout << ", frameType=" << vsStatus.frameType;
			cout << ", colorFormat=" << vsStatus.colorFormat;
			cout << ", quantRange=" << vsStatus.quantRange;
			cout << ", satRange=" << vsStatus.satRange;
			cout << ". frameRate=" << frameRate;
			cout << endl;
		}

		if (  ( cx > 0 ) && ( cx  < 9999 ) && (cy > 0) && (cy < 9999)) {
			if (recording == 0) {
				// find target video device name/path when not specified explicitly
				if( cfg.ffm_opts.has_v_dev ) {
					targetVideoDevPath = cfg.ffm_opts.v_dev;
				} else {
					targetVideoDevPath = getVideoDevicePathBySerial(opts.verbose,
																	cfg.video_device_path_pattern,
																	targetDevSerial);
					if( targetVideoDevPath.empty() ) {
						targetVideoDevPath = "/dev/video_not_found_911";
						cerr << "ERROR[007]: video device path not found by S/N: " << targetDevSerial
							 << ", use fallback one: " << targetVideoDevPath << endl;
					}
				}

				if( !cfg.ffm_opts.has_v_dev || !cfg.has_device_serial_number ) {
					cout << "    <> Found Video Device          ===> "
						 << targetVideoDevPath << ", S/N: " << targetDevSerial
						 << ", " << targetDevName << endl;
				}

				startRecording(cfg, cx, cy, frameRate, start_str,
							   opts.outPath, targetVideoDevPath);
				recording = 1;
				cout << start_str << ":\tStarted Recording: " << endl;
				cout << "Apct Rat: " << cx << "x" << cy << endl;
				cout << "FR: " << frameRate << endl;
				usleep(5000000);
			}
			else {
				if (( state != prev_state ) ||
					( cx != prev_cx ) || (cy != prev_cy) ||
					( cxTotal != prev_cxTotal ) ||
					( cyTotal != prev_cyTotal ) ||
					( bInterlaced != prev_bInterlaced ) ||
					( dwFrameDuration != prev_dwFrameDuration ) ||
					( nAspectX != prev_nAspectX ) ||
					( nAspectY != prev_nAspectY ) ||
					( bSegmentedFrame != prev_bSegmentedFrame ) ||
					( frameType != prev_frameType ) ||
					( colorFormat != prev_colorFormat ) ||
					( quantRange != prev_quantRange ) ||
					( satRange != prev_satRange )) {
					getTimeStr(stop_str);
					cout << stop_str;
					cout << ":\tStopped recording because something changed."<<endl;
					stopRecording(start_str, opts.outPath);
					nMov++;
					recording = 0;
				}
			}
		}
		else {
			if( opts.verbose ) {
				cout << "No valid video signal detected from target device" << endl;
			}

			if (recording == 1) {
				getTimeStr(stop_str);
				cout << stop_str;
				cout << ":\tWhack resolution: " << cx << "x" << cy;
				cout << ". Stopped recording" << endl;
				stopRecording(start_str, opts.outPath);
				nMov++;
				recording = 0;
			}
		}

		prev_state = state;


		prev_cx = cx;
		prev_cy = cy;
		prev_cxTotal = cxTotal;
		prev_cyTotal = cyTotal;
		prev_bInterlaced = bInterlaced;
		prev_dwFrameDuration = dwFrameDuration;
		prev_nAspectX = nAspectX;
		prev_nAspectY = nAspectY;
		prev_bSegmentedFrame = bSegmentedFrame;
		prev_frameType = frameType;
		prev_colorFormat = colorFormat;
		prev_quantRange = quantRange;
		prev_satRange = satRange;

		if (hChannel != NULL) {
			MWCloseChannel(hChannel);
			hChannel = NULL;
		}
	} while ( true );

	stopRecording(start_str, opts.outPath);

	if( fInit )
		MWCaptureExitInstance();
	return 0;
}