﻿/************************************************************************************************/
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
#include <sys/stat.h>
#include <fcntl.h>
#include <ctime>
#include <cmath>
#include "LibMWCapture/MWCapture.h"
#include "LibMWCapture/MWUSBCapture.h"
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>
#include <array>
#include <cstring>
#include "yaml-cpp/yaml.h"
#pragma GCC diagnostic ignored "-Wwrite-strings"

using namespace std;

std::string exec(const char* cmd) {
	std::array<char, 128> buffer;
	std::string result;
	std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
	if (!pipe) {
		throw std::runtime_error("popen() failed!");
	}
	while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
		result += buffer.data();
	}
	cout << "exec says:  " << result << endl;
	return result;
}



void get_time_str(char mov[256]){
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

static void stop_recording(char start_str[256], char vpath[256]) {
	std::string ffmpid;
	ffmpid = exec("pidof ffmpeg");
	cout << "stop record says: " << ffmpid.c_str() << endl;
	while ( ffmpid.length() > 0 ) {
		cout << "<> PID of ffmpeg\t===> " << ffmpid.c_str() << endl;
		char stop_str[256] = {0};
		get_time_str(stop_str);
		char killCmd[256] = {0}; 
		sprintf(killCmd, "kill -9 %s", ffmpid.c_str());
		system(killCmd);
		char oldname[256] = {0};
		char newname[512] = {0};
		sprintf(oldname, "%s/%s_.mkv", vpath, start_str);
		sprintf(newname, "%s/%s_%s.mkv", vpath, start_str, stop_str);
		cout << stop_str << ":\tKilling " << ffmpid.c_str() << ". Saving video ";
		cout << newname << endl;
		int x = 0;
		x = rename(oldname, newname);
		usleep(1500000); // Allow time for ffmpeg to stop
		ffmpid = exec("pidof ffmpeg");
	}
}

void start_recording(YAML::Node cfg, int cx, int cy, char fr[256], char starttime[256],
		char vpath[256]){
	get_time_str(starttime);
	char ffmpg[1024] = {0};
	string a_fmt = cfg["a_fmt"].as<string>();
	string a_nchan = cfg["a_nchan"].as<string>();
	string a_opt = cfg["a_opt"].as<string>();
	string a_dev = cfg["a_dev"].as<string>();
	string v_fmt = cfg["v_fmt"].as<string>();
	string v_opt = cfg["v_opt"].as<string>();
	string v_dev = cfg["v_dev"].as<string>();
	string v_enc = cfg["v_enc"].as<string>();
	string pix_fmt = cfg["pix_fmt"].as<string>();
	string n_threads = cfg["n_threads"].as<string>();
	string a_enc = cfg["a_enc"].as<string>();
	string out_fmt = cfg["out_fmt"].as<string>();

	sprintf(ffmpg, "ffmpeg %s %s %s %s %s -framerate %s -video_size %ix%i %s -i %s "
			"%s %s %s %s %s/%s_.%s > /dev/null &", 
		a_fmt.c_str(),
		a_nchan.c_str(),
		a_opt.c_str(),
		a_dev.c_str(),
		v_fmt.c_str(),
		fr, 
		cx, 
		cy, 
		v_opt.c_str(),
		v_dev.c_str(),
		v_enc.c_str(),
		pix_fmt.c_str(),
		n_threads.c_str(),
		a_enc.c_str(),
		vpath, 
		starttime,
		out_fmt.c_str());

	cout << starttime;
	cout << ": <SYSTEMCALL> " << ffmpg << endl;
	system(ffmpg);
}

int main(int argc, char* argv[]){
	
	const char* helpstr="Usage: VideoCapture -d <path> [-o <path> | -h | -v ]\n\n"
		"\t-d <path>\t$REPROSTIM_HOME directory (not optional)\n"
		"\t-o <path>\tOutput directory where to save recordings (optional)\n"
		"\t         \tDefaults to $REPROSTIM_HOME/Videos\n"
		"\t-c <path>\tPath to configuration config.yaml file (optional)\n"
		"\t         \tDefaults to $REPROSTIM_HOME/config.yaml\n"
		"\t-v       \tVerbose, provides detailed information to stdout\n"
		"\t-h       \tPrint this help string\n";
	bool verbose = false;
	char * vpath = NULL;
	char * cfg_fn = NULL;
	char * rep_hm = NULL;
	char video_path[256] = "";

	int c = 0;
	if (argc == 1){ 
		cout << helpstr << endl;
		return 55;
	}

	while( ( c = getopt (argc, argv, "d:o:c:h:v") ) != -1 ){
		switch(c){
		case 'o':
			if(optarg) vpath = optarg;
			break;
		case 'c':
			if(optarg) cfg_fn = optarg;
			break;
		case 'd':
			if(optarg) rep_hm = optarg;
			break;
		case 'h':
			cout << helpstr << endl;
			return 0;
		case 'v':
			verbose = true;
			break;
		}
	}

	// Puke if Repro Home not specified
	if ( ! rep_hm ){
		cout << helpstr << endl;
		return 55;
	}

	// Set config filename if not specified on input
	if ( ! cfg_fn ){
		char c_fn[256]; 
		sprintf(c_fn, "%s/config.yaml", rep_hm);
		cfg_fn = c_fn;
	}
	cout << "Config file: " << cfg_fn << endl;
	YAML::Node config = YAML::LoadFile(cfg_fn);
	
	// Set output directory if not specified on input
	if ( ! vpath ){
		char sufx[] = "/Videos";
		strcat(video_path, rep_hm);
		strcat(video_path, sufx);
		vpath = video_path;
	}	

	if ( verbose ) {
		cout << "Output path: " << vpath << endl;
	}

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

	get_time_str(init_time);
	cout << init_time;
	cout << ": <><><> Starting VideoCapture <><><>" << endl;	
	
	cout << "\t<> Saving Videos to\t\t===> " << vpath << endl;;
	cout << "\t<> Recording from Video Device\t===> ";
	cout << config["ffm_opts"]["v_dev"] << endl;

	do {
		usleep(1000000);
		BOOL fInit = MWCaptureInitInstance();
		if( !fInit )
			cerr << "ERROR[005]: Failed MWCaptureInitInstance" << endl;
		HCHANNEL hChannel = NULL;
		MW_RESULT mwRes = MWRefreshDevice();
		if( mwRes!=MW_SUCCEEDED )
			cerr << "ERROR[004]: Failed MWRefreshDevice: " << mwRes << endl;
		int nCount = MWGetChannelCount();

		if( verbose )
			cout << "Channel count: " << nCount << endl;

		if (nCount <= 0) {
			cout << "ERROR[001]: Can't find channels!" << endl;
			if ( recording > 0 ){
				get_time_str(stop_str);
				stop_recording(start_str, vpath);
				recording = 0;
				cout << stop_str << ":\tStopped recording. No channels!"<<endl;
				nMov++;
			}
			continue;	
		}
	
		int nUsbCount = 0;
		int nUsbDevice[16] = {-1};
	
		for (int i = 0; i < nCount; i++){
			
			MWCAP_CHANNEL_INFO info;
			mr = MWGetChannelInfoByIndex(i, &info);

			if( verbose ) {
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
				if( verbose ) {
					cout << "Found USB Capture device, index=" << i << endl;
				}
				nUsbDevice[nUsbCount] = i;
				nUsbCount ++;
			} else {
				if (info.wProductID == 0 && info.wFamilyID == 0) {
					cerr << "ERROR[003]: Access or permissions issue. Please check /etc/udev/rules.d/ configuration and docs." << endl;
					if (recording > 0) {
						get_time_str(stop_str);
						stop_recording(start_str, vpath);
						recording = 0;
						cout << stop_str << ":\tStopped recording. No channels!" << endl;
						nMov++;
					}
					return -56; // TODO: break or continue execution?
				} else {
					if( verbose ) {
						cout << "Unknown USB device, skip it, index=" << i << endl;
					}
				}
			}
		}
	
		char wPath[256] = {0};
		mr = MWGetDevicePath(nUsbDevice[0], wPath);
		if( verbose )
			cout << "device path: " << wPath << endl;
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

		if( verbose ) {
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
				start_recording(config["ffm_opts"], cx, cy, 
						frameRate, start_str, vpath);
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
				get_time_str(stop_str);
				cout << stop_str;
				cout << ":\tStopped recording because something changed."<<endl;
				stop_recording(start_str, vpath);
				nMov++;
				recording = 0;
				}	
			}
		}
		else {
			if( verbose ) {
				cout << "No valid video signal detected from target device" << endl;
			}

			if (recording == 1) {
				get_time_str(stop_str);
				cout << stop_str;
				cout << ":\tWhack resolution: " << cx << "x" << cy;
				cout << ". Stopped recording" << endl;
				stop_recording(start_str, vpath);
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
		
		MWCaptureExitInstance();
	} while ( true ); 

	stop_recording(start_str, vpath);
	return 0;
}
