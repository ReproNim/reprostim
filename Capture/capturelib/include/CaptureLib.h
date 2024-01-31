#ifndef REPROSTIM_CAPTURELIB_H
#define REPROSTIM_CAPTURELIB_H

#include <string>
#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include "LibMWCapture/MWCapture.h"
#include "CaptureVer.h"

/*########################### Common macros ############################*/

#ifndef _ERROR
#define _ERROR(expr) std::cerr << expr << std::endl
#endif

#ifndef _INFO
#define _INFO(expr) std::cout << expr << std::endl
#endif

#ifndef _INFO_RAW
#define _INFO_RAW(expr) std::cout << expr
#endif

#ifndef _VERBOSE
#define _VERBOSE(expr) if( verbose ) { std::cout << expr << std::endl; }
#endif

#ifndef PATH_MAX_LEN
#define PATH_MAX_LEN 1024
#endif

#ifndef SLEEP_MS
#define SLEEP_MS(ms) std::this_thread::sleep_for(std::chrono::milliseconds(ms))
#endif

#ifndef SLEEP_SEC
#define SLEEP_SEC(sec) SLEEP_MS(static_cast<int>(sec*1000))
#endif


#define EX_SYS_BREAK_EXEC		140	/* custom exit code when execution broken by Ctrl+C, SIGINT or similar events */
#define EX_CONFIG_RELOAD		141	/* custom exit code when config.yaml file changed */

namespace reprostim {

	struct VDevSerial {
		std::string serialNumber;
		std::string busInfo;
	};

	struct VDevPath {
		std::string path;
		std::string busInfo;
	};

	struct VideoDevice {
		std::string name;
		std::string serial;
		int channelIndex = -1;
	};

	bool checkOutDir(bool verbose, const std::string &outDir);

	int checkSystem(bool verbose);

	std::string chiToString(MWCAP_CHANNEL_INFO &info);

	std::string exec(bool verbose, const std::string &cmd, bool showStdout = false);

	bool findTargetVideoDevice(bool verbose, const std::string &serialNumber, VideoDevice &vd);

	std::string getAudioDevicePath(bool verbose, const std::string &busInfo);

	// get file hash info in string format representing unique file snapshot in time
	std::string getFileChangeHash(const std::string &filePath);

	std::vector<std::string> getVideoDevicePaths(const std::string &pattern);

	// NOTE: uses by-value result
	VDevSerial getVideoDeviceSerial(bool verbose, const std::string &devPath);

	// NOTE: uses by-value result
	VDevPath getVideoDevicePathBySerial(bool verbose, const std::string &pattern, const std::string &serial);

	std::string getTimeStr();

	bool isSysBreakExec();

	std::string mwcSdkVersion();

	void safeMWCloseChannel(HCHANNEL&hChannel);

	void setSysBreakExec(bool fBreak);

	std::string vdToString(VideoDevice &vd);

	// Video signal status helpers
	std::string vssFrameRate(const MWCAP_VIDEO_SIGNAL_STATUS &vss);

	bool vssEquals(const MWCAP_VIDEO_SIGNAL_STATUS &vss1,
				   const MWCAP_VIDEO_SIGNAL_STATUS &vss2);

	std::string vssToString(const MWCAP_VIDEO_SIGNAL_STATUS &vsStatus);

	// inline functions
	inline long long currentTimeMs() {
		return std::chrono::duration_cast<std::chrono::milliseconds>(
				std::chrono::system_clock::now().time_since_epoch()
		).count();
	}


}
#endif //REPROSTIM_CAPTURELIB_H
