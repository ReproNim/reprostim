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
		sprintf(oldname, "%s/%s_.mp4", vpath, start_str);
		sprintf(newname, "%s/%s_%s.mp4", vpath, start_str, stop_str);
		cout << stop_str << ":\tKilling " << ffmpid.c_str() << ". Saving video ";
		cout << newname << endl;
		int x = 0;
		x = rename(oldname, newname);
		usleep(1500000); // Allow time for ffmpeg to stop
		ffmpid = exec("pidof ffmpeg");
	}
}

void start_recording(int cx, int cy, char fr[256], char starttime[256], 
		char capdev[256], char vpath[256]){
	get_time_str(starttime);
	char ffmpg[1024] = {0};
	cout << starttime;	
	cout << ": <SYSTEMCALL> ffmpeg -f alsa -i hw:1,1 -framerate ";
	cout << fr << " -video_size " << cx << "x" << cy << endl;
        cout << "\t -i " << capdev << " " << vpath << "/" << starttime << "_.mp4" <<endl;	
	sprintf(ffmpg, "ffmpeg -f alsa -i hw:1,1 -framerate %s -video_size %ix%i " 
		"-i %s %s/%s_.mp4 > /dev/null 2>&1 &", fr, cx, cy, capdev, vpath, starttime);
	system(ffmpg);
}

int main(int argc, char* argv[]){
	const char* helpstr="usage: ./VideoCapture -o <path> [-d <path> | -h ]\n"
		"\t-o <path>\tOutput directory where to save recordings (not optional)\n"
		"\t-d <path>\tPath to capture device (default = '/dev/video0', opt)\n"
		"\t-h\t\tPrint this help string\n";
	char* vpath = NULL ;	
	char* capdev = "/dev/video0";
	int c ;
	if (argc == 1){ 
		cout << helpstr << endl;
		return 55;
	}

	while( ( c = getopt (argc, argv, "o:d:h") ) != -1 ){
		switch(c){
		case 'o':
			if(optarg) vpath = optarg;
			//cout<<typeid(optarg).name()<<endl;
			break;
		case 'd':
			if(optarg) capdev = optarg;
			break;
		case 'h':
			cout << helpstr << endl;
			return 55;
		}
	}

	// Puke if vpath not specified
	if ( ! vpath ){
		cout << helpstr << endl;
		return 55;
	}


	MWCAP_VIDEO_SIGNAL_STATE state;
	int x = 0;
	int y = 0;	
	int cx = 0;	
	int cy = 0;
	int cxTotal = 0;
	int cyTotal = 0;
	BOOLEAN bInterlaced;
	DWORD dwFrameDuration;
	int nAspectX = 0;
	int nAspectY = 0;
	BOOLEAN bSegmentedFrame;
	MWCAP_VIDEO_FRAME_TYPE frameType;
	MWCAP_VIDEO_COLOR_FORMAT colorFormat;
	MWCAP_VIDEO_QUANTIZATION_RANGE quantRange;
	MWCAP_VIDEO_SATURATION_RANGE satRange;

	MWCAP_VIDEO_SIGNAL_STATE prev_state;
	int prev_x = 0;
	int prev_y = 0;	
	int prev_cx = 0;	
	int prev_cy = 0;
	int prev_cxTotal = 0;
	int prev_cyTotal = 0;
	BOOLEAN prev_bInterlaced;
	DWORD prev_dwFrameDuration;
	int prev_nAspectX = 0;
	int prev_nAspectY = 0;
	BOOLEAN prev_bSegmentedFrame;
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
	cout << "\t<> Recording from Video Device\t===> " << capdev << endl;


	do {
		usleep(1000000);
		cout << "done sleeping" << endl;
		MWCaptureInitInstance();
		HCHANNEL hChannel = NULL;
		MWRefreshDevice();
		int nCount = MWGetChannelCount();

		if (nCount <= 0){
			//printf("ERROR: Can't find channels!\n");
			cout << "Error: Can't find channels!" << endl;
			if ( recording > 0 ){
				get_time_str(stop_str);
				stop_recording(start_str, vpath);
				recording = 0;
				cout << stop_str << ":\tStopped recording. No channels!"<<endl;
				//printf("%s: stopped recoding b/c no channels!\n", stop_str);
				nMov++;
			}
			continue;	
		}

		int nUsbCount = 0;
		int nUsbDevice[16] = {-1};
		for (int i = 0; i < nCount; i++){
			MWCAP_CHANNEL_INFO info;
			mr = MWGetChannelInfoByIndex(i, &info);
			//printf("MR: %i\n", mr);
			//printf("SZFamName : %s\n", info.szFamilyName);
			if (strcmp(info.szFamilyName, "USB Capture") == 0) {
				nUsbDevice[nUsbCount] = i;
				nUsbCount ++;
			}
		}

		char wPath[256] = {0};
		// printf("nUsbDevice : %d\n", nUsbDevice[0]);
		mr = MWGetDevicePath(nUsbDevice[0], wPath);
		hChannel = MWOpenChannelByPath(wPath);

		//printf("Device Path : %s\n", wPath);
		//printf("argc : %d\n", argc);

		MWCAP_VIDEO_SIGNAL_STATUS thisInfo;
		MWGetVideoSignalStatus(hChannel, &thisInfo);

		state = thisInfo.state;
		x = thisInfo.x;
		y = thisInfo.y;	
		cx = thisInfo.cx;	
		cy = thisInfo.cy;
		cxTotal = thisInfo.cxTotal;
		cyTotal = thisInfo.cyTotal;
		bInterlaced = thisInfo.bInterlaced;
		dwFrameDuration = thisInfo.dwFrameDuration;
		nAspectX = thisInfo.nAspectX;
		nAspectY = thisInfo.nAspectY;
		bSegmentedFrame = thisInfo.bSegmentedFrame;
		frameType = thisInfo.frameType;
		colorFormat = thisInfo.colorFormat;
		quantRange = thisInfo.quantRange;
		satRange = thisInfo.satRange;

		sprintf(frameRate, "%.0f", round( 10000000./dwFrameDuration));	

		if (  ( cx > 0 ) && ( cx  < 9999 ) && (cy > 0) && (cy < 9999)) {
			if (recording == 0) {
				start_recording(cx, cy, frameRate, start_str, capdev, vpath);
			recording = 1;
			cout << start_str << ":\tStarted Recording" << endl;
			//printf("%s: started recording\n", start_str);
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
					//printf("%s: stopped recording because something changed.\n", stop_str);
					stop_recording(start_str, vpath);
					nMov++;
					recording = 0;
				}	
			}
		}
		else {
			if (recording == 1) {
				get_time_str(stop_str);
				cout << stop_str;
				cout << ":\tWhack resolution: " << cx << "x" << cy;
				cout << ". Stopped recording" << endl;
				//printf("%s: Whack resolution: stopped recording.%i x %i \n", stop_str, cx, cy);
				stop_recording(start_str, vpath);
				nMov++;
				recording = 0;
			}
		}
		prev_state = state;
		prev_x = x;
		prev_y = y;	
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
