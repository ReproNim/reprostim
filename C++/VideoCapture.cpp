/************************************************************************************************/
// VideoCapture.cpp : Detects if device connected or changes state, if video input available,
// then it also reports the resolution, frame rate, and any changes there of.
//
// This code is adapted and modified from the Magewell example code cited below. All licensing
// and legal matters pertaining thereunto are stipulated in the text below which has been preserved 
// from the original Magewell distribution.
//
// Code bastardizer: Andy Connolly : andrew.c.connolly@dartmouth.edu
// date of bastardization inception: 01/15/2020
//
// Original header begins after this line.

// USBDeviceDetect.cpp : Defines the entry point for the console application.

// MAGEWELL PROPRIETARY INFORMATION

// The following license only applies to head files and library within Magewell’s SDK 
// and not to Magewell’s SDK as a whole. 

// Copyrights © Nanjing Magewell Electronics Co., Ltd. (“Magewell”) All rights reserved.

// Magewell grands to any person who obtains the copy of Magewell’s head files and library 
// the rights,including without limitation, to use, modify, publish, sublicense, distribute
// the Software on the conditions that all the following terms are met:
// - The above copyright notice shall be retained in any circumstances.
// -The following disclaimer shall be included in the software and documentation and/or 
// other materials provided for the purpose of publish, distribution or sublicense.

// THE SOFTWARE IS PROVIDED BY MAGEWELL “AS IS” AND ANY EXPRESS, INCLUDING BUT NOT LIMITED TO,
// THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
// IN NO EVENT SHALL MAGEWELL BE LIABLE 

// FOR ANY CLAIM, DIRECT OR INDIRECT DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT,
// TORT OR OTHERWISE, ARISING IN ANY WAY OF USING THE SOFTWARE.

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


pid_t system2(const char * command, int * infp, int * outfp)
{
	//std::fstream fs;
    int p_stdin[2];
    int p_stdout[2];
    pid_t pid;

    if (pipe(p_stdin) == -1)
        return -1;

    if (pipe(p_stdout) == -1) {
        close(p_stdin[0]);
        close(p_stdin[1]);
        return -1;
    }

    pid = fork();

    if (pid < 0) {
        close(p_stdin[0]);
        close(p_stdin[1]);
        close(p_stdout[0]);
        close(p_stdout[1]);
        return pid;
    } else if (pid == 0) {
        close(p_stdin[1]);
        dup2(p_stdin[0], 0);
        close(p_stdout[0]);
        dup2(p_stdout[1], 1);
        dup2(open("/dev/null", O_RDONLY), 2);
        /// Close all other descriptors for the safety sake.
        for (int i = 3; i < 4096; ++i)
            close(i);

        setsid();
        execl("/bin/sh", "sh", "-c", command, NULL);
        _exit(1);
    }

    close(p_stdin[0]);
    close(p_stdout[1]);

    if (infp == NULL) {
        close(p_stdin[1]);
    } else {
        *infp = p_stdin[1];
    }

    if (outfp == NULL) {
        close(p_stdout[0]);
    } else {
        *outfp = p_stdout[0];
    }


    return pid;
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

static void stop_recording(int pid, char start_str[256]) {
	char stop_str[256] = {0};
	get_time_str(stop_str);
	
	char killCmd[256] = {0}; 
	sprintf(killCmd, "kill -INT %d", pid);
	system(killCmd);

	char oldname[256] = {0};
	char newname[256] = {0};
	sprintf(oldname, "../Videos/%s_.mkv", start_str);
	sprintf(newname, "../Videos/%s_%s.mkv", start_str, stop_str);
	printf("%s: Saving video %s\n", stop_str, newname);
	int x = 0;
	x = rename(oldname, newname);
	usleep(1500000); // Allow time for ffmpeg to stop
}

pid_t start_recording(int cx, int cy, char starttime[256]){


	get_time_str(starttime);
	char ffmpg[1024] = {0};
	printf("%s: <SYSTEMCALL> ffmpeg -y -f v4l2 -framerate 60 -video_size %ix%i \n" 
				   "\t -i /dev/video0 ../Videos/%s_.mkv \n", starttime, cx, cy, starttime);
	

	sprintf(ffmpg, "ffmpeg -y -f v4l2 -framerate 60 -video_size %ix%i " 
				   "-i /dev/video0 ../Videos/%s_.mkv ", cx, cy, starttime);
	
	// Call ffmpeg
	int pid = 0;
	pid = system2(ffmpg,0,0);

	//printf(ffmpg);	

	return pid;
	
}




int main(int argc, char* argv[])
{

	
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
	int ffmpeg_pid = 0;
	char start_str[256] = {0};
	char stop_str[256] = {0};	
	int nMov = 0;	

	MW_RESULT mr = MW_SUCCEEDED;	

	do {
		
		usleep(1000000);
		MWCaptureInitInstance();

		HCHANNEL hChannel = NULL;
    	//MW_RESULT mr = MW_SUCCEEDED;
        MWRefreshDevice();


        int nCount = MWGetChannelCount();
		if (nCount <= 0){
            //printf("ERROR: Can't find channels!\n");
			if ( recording > 0 ){
				get_time_str(stop_str);
				stop_recording(ffmpeg_pid, start_str);
				recording = 0;
				printf("%s: stopped recoding b/c no channels!\n", stop_str);
				nMov++;
			}
			continue;	
        }
		
		

        //printf("Log: Find %d channels!\n",nCount);
        int nUsbCount = 0;
        int nUsbDevice[16] = {-1};
        for (int i = 0; i < nCount; i++){
            MWCAP_CHANNEL_INFO info;
            mr = MWGetChannelInfoByIndex(i, &info);
            if (strcmp(info.szFamilyName, "USB Capture") == 0) {
                nUsbDevice[nUsbCount] = i;
                nUsbCount ++;
            }
        }
        //MW_RESULT mr = MW_SUCCEEDED;

        

		char wPath[256] = {0};
		//printf("nUsbDevice : %d\n", nUsbDevice[0]);
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




	    printf("%d %.0f \n", thisInfo.bInterlaced, round( 10000000./thisInfo.dwFrameDuration));	

		//printf("----------------------------------------\nvalue of cx : %d\n", cx);
		//printf("value of cy : %d\n", cy);
		//printf("value of prev cx : %d\n", prev_cx);
		//printf("value of prev cy : %d\n", prev_cy);
		//printf("Value of recording : %d\n", recording);


		if (  ( cx > 0 ) && ( cx  < 9999 ) && (cy > 0) && (cy < 9999)) 
		{
			if (recording == 0) 
			{
				ffmpeg_pid = start_recording(cx, cy, start_str);
				recording = 1;
				printf("%s: started recording\n", start_str);
				usleep(5000000);
			}
			
			else 
			{
				if 	(	( state != prev_state ) ||
						( x != prev_x ) || 
						( y != prev_y ) ||
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
						( satRange != prev_satRange )  
					) 
					{
					get_time_str(stop_str);
					printf("%s: stopped recording because something changed.\n", stop_str);
					stop_recording(ffmpeg_pid, start_str);
					nMov++;
					recording = 0;
					}	
			}
		}
		else {
			
			if (recording == 1) {
				get_time_str(stop_str);
				printf("%s: Whack resolution: stopped recording.%i x %i \n", stop_str, cx, cy);
				stop_recording(ffmpeg_pid, start_str);
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

		//printf("value of nMov : %d\n", nMov);

    if (hChannel != NULL) {
        MWCloseChannel(hChannel);
        hChannel = NULL;
    }

		MWCaptureExitInstance();

		} while ( nMov < 5); 
	stop_recording(ffmpeg_pid, start_str);


    return 0;
}

