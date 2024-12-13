#ifndef REPROSTIM_CAPTURELIB_H
#define REPROSTIM_CAPTURELIB_H

#include <string>
#include <functional>
#include <iostream>
#include <memory>
#include <sstream>
#include <vector>
#include <chrono>
#include <thread>
#include <cmath>
#include "LibMWCapture/MWCapture.h"
#include "reprostim/CaptureVer.h"
#include "reprostim/CaptureLog.h"

/*########################### Common macros ############################*/


// hardcoded audio sub device to Line-In by default
#ifndef DEFAULT_AUDIO_IN_DEVICE
#define DEFAULT_AUDIO_IN_DEVICE "1"
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

// current TIMESTAMP value
#ifndef CURRENT_TIMESTAMP
#define CURRENT_TIMESTAMP() std::chrono::system_clock::now()
#endif


#define EX_SYS_BREAK_EXEC		140	/* custom exit code when execution broken by Ctrl+C, SIGINT or similar events */
#define EX_CONFIG_RELOAD		141	/* custom exit code when config.yaml file changed */

namespace reprostim {

	//////////////////////////////////////////////////////////////////////////
	// Enums

	enum VolumeLevelUnit: int {
		RAW     = 0,
		PERCENT = 1,
		DB      = 2 // not supported yet
	};

	//////////////////////////////////////////////////////////////////////////
	// Typedefs

	// Define std::string to std::string dictionary type
	using SDict = std::unordered_map<std::string, std::string>;

	// define timestamp type in reprostim terms and precision
	// because in C++ there is no normal stable built-in timestamp
	// type ATM
	using Timestamp = std::chrono::system_clock::time_point;

	//////////////////////////////////////////////////////////////////////////
	// Structs

	struct AudioInDevice {
		std::string  alsaCardName;
		std::string  alsaDeviceName;
		std::string  cardId;
		std::string  deviceId;
	};

	struct AudioVolume {
		std::string     label;
		float           level = 0.0;
		VolumeLevelUnit unit = VolumeLevelUnit::RAW;

		inline long getLevelAsLong() const {
			return static_cast<long>(std::round(level));
		}
	};

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

	//////////////////////////////////////////////////////////////////////////
	// Functions

	bool checkOutDir(const std::string &outDir);

	int checkSystem();

	std::string chiToString(const MWCAP_CHANNEL_INFO &info);

	std::string exec(const std::string &cmd, bool showStdout = false,
					 bool sessionLogOnly = false, int maxResLen = -1,
					 std::function<bool()> isTerminated = [](){ return false; });

	std::string expandMacros(const std::string &text, const SDict &dict);

	bool findTargetVideoDevice(const std::string &serialNumber, VideoDevice &vd);

	// returns audio device ALSA path and sound card ALSA name
	AudioInDevice getAudioInDevice(const std::string &busInfo,
								   const std::string &device);

	std::string getAudioInNameByAlias(const std::string &alias);

	std::string getDefaultAudioInDeviceByCard(const std::string &alsaCardName);

	// get file hash info in string format representing unique file snapshot in time
	std::string getFileChangeHash(const std::string &filePath);

	std::vector<std::string> getVideoDevicePaths(const std::string &pattern);

	// NOTE: uses by-value result
	VDevSerial getVideoDeviceSerial(const std::string &devPath);

	// NOTE: uses by-value result
	VDevPath getVideoDevicePathBySerial(const std::string &pattern, const std::string &serial);

	// Date-time format historically used in reprostim
	// e.g. "2024.03.02.12.33.08.006"
	std::string getTimeStr(const Timestamp &ts = CURRENT_TIMESTAMP());

	// Format date/time with strftime-like pattern
	std::string getTimeFormatStr(const Timestamp &ts = CURRENT_TIMESTAMP(),
								 const std::string &format = "%Y-%m-%d %H:%M:%S");

	// ISO 8601 date-time string conversion with microseconds
	// precision and "no time-zone" information
	// e.g. "2024-03-17T17:13:53.478287"
	std::string getTimeIsoStr(const Timestamp &ts = CURRENT_TIMESTAMP());

	bool isSysBreakExec();

	void listAudioDevices();

	void listVideoDevices();

	std::string mwcSdkVersion();

	AudioVolume parseAudioVolume(const std::string text);

	void safeMWCloseChannel(HCHANNEL &hChannel);

	void setAudioInVolumeByCard(const std::string &alsaCardName,
								const std::unordered_map<std::string, AudioVolume> &mapNameVolume);

	void setSysBreakExec(bool fBreak);

	std::string vdToString(const VideoDevice &vd);

	// Video signal status helpers
	std::string vssFrameRate(const MWCAP_VIDEO_SIGNAL_STATUS &vss);

	bool vssEquals(const MWCAP_VIDEO_SIGNAL_STATUS &vss1,
				   const MWCAP_VIDEO_SIGNAL_STATUS &vss2);

	std::string vssToString(const MWCAP_VIDEO_SIGNAL_STATUS &vsStatus);

	//////////////////////////////////////////////////////////////////////////
	// inline functions
	inline long long currentTimeMs() {
		return std::chrono::duration_cast<std::chrono::milliseconds>(
				std::chrono::system_clock::now().time_since_epoch()
		).count();
	}

	// get std::string representation of time year in format "YYYY"
	inline std::string getTimeYearStr(const Timestamp &ts = CURRENT_TIMESTAMP()) {
		return getTimeFormatStr(ts, "%Y");
	}

	// get std::string representation of time month in format "MM"
	inline std::string getTimeMonthStr(const Timestamp &ts = CURRENT_TIMESTAMP()) {
		return getTimeFormatStr(ts, "%m");
	}

	inline std::ostream& operator<<(std::ostream& os, const MWCAP_CHANNEL_INFO &chi) {
		os << chiToString(chi);
		return os;
	}

	inline std::ostream& operator<<(std::ostream& os, const MWCAP_VIDEO_SIGNAL_STATUS &vss) {
		os << vssToString(vss);
		return os;
	}

	inline std::ostream& operator<<(std::ostream& os, const VideoDevice &vd) {
		os << vdToString(vd);
		return os;
	}

}
#endif //REPROSTIM_CAPTURELIB_H
