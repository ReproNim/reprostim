#include <iostream>
#include <iomanip>
#include <sstream>
#include <filesystem>
#include <stdio.h>
#include <string.h>
#include <glob.h>
#include <ctime>
#include <cmath>
#include <stdexcept>
#include <string>
#include <regex>
#include <array>
#include <csignal>
#include <sysexits.h>
#include <alsa/asoundlib.h>
#include "CaptureLib.h"

namespace fs = std::filesystem;

namespace reprostim {

	// private static global flag
	static volatile sig_atomic_t s_nSysBreakExec = 0;

	bool checkOutDir(bool verbose, const std::string &outDir) {
		if (!fs::exists(outDir)) {
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

	int checkSystem(bool verbose) {
		// check ffmpeg
		std::string ffmpeg = exec(false, "which ffmpeg");
		if (ffmpeg.empty()) {
			_ERROR("ffmpeg program not found. Please make sure ffmpeg package is installed.");
			return EX_UNAVAILABLE;
		}

		// check v4l2-ctl
		std::string v4l2ctl = exec(false, "which v4l2-ctl");
		if (v4l2ctl.empty()) {
			_ERROR("v4l2-ctl program not found. Please make sure v4l-utils package is installed.");
			return EX_UNAVAILABLE;
		}

		return EX_OK;
	}

	std::string chiToString(MWCAP_CHANNEL_INFO &info) {
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

	std::string exec(bool verbose, const std::string &cmd, bool showStdout) {
		std::array<char, 128> buffer;
		std::string result;
		std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
		if (!pipe) {
			_ERROR("popen() failed for cmd: " << cmd);
			throw std::runtime_error("popen() failed!");
		}
		while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
			result += buffer.data();
			if (showStdout) {
				_INFO_RAW(buffer.data());
				fflush(stdout); // force output
			}
		}
		_VERBOSE("exec -> :  " << result);
		return result;
	}

	bool findTargetVideoDevice(bool verbose,
							   const std::string &serialNumber,
							   VideoDevice &vd) {
		vd.channelIndex = -1;
		MW_RESULT mwRes = MWRefreshDevice();
		if (mwRes != MW_SUCCEEDED) {
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
				if (!serialNumber.empty()) {
					if (serialNumber == info.szBoardSerialNo) {
						_VERBOSE("Found USB Capture device with S/N=" << info.szBoardSerialNo << " , index=" << i);
						vd.serial = info.szBoardSerialNo;
						vd.name = info.szProductName;
						vd.channelIndex = i;
						return true;
					} else {
						_VERBOSE("Unknown USB device with S/N=" << info.szBoardSerialNo << ", skip it, index=" << i);
					}
				} else {
					_VERBOSE("Found USB Capture device, index=" << i);
					vd.serial = info.szBoardSerialNo;
					vd.name = info.szProductName;
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

	std::string getAudioDevicePath(bool verbose, const std::string &busInfo) {
		std::string res;

		snd_ctl_t *handle;
		snd_ctl_card_info_t *info;
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

			if (snd_ctl_card_info(handle, info) >= 0) {
				std::string id = snd_ctl_card_info_get_id(info);
				std::string name = snd_ctl_card_info_get_name(info);
				std::string lname = snd_ctl_card_info_get_longname(info);
				//_VERBOSE("Card " << int(card) << ": id=" << id << ", name=" << name << ", lname=" << lname);
				snd_ctl_close(handle);

				if (name.find("USB Capture") != std::string::npos) {
					if (!busInfo.empty() &&
						lname.find(busInfo) != std::string::npos &&
						lname.find("Magewell") != std::string::npos) {
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

// get file hash info in string format representing unique file snapshot in time
	std::string getFileChangeHash(const std::string &filePath) {
		std::filesystem::file_time_type mt = std::filesystem::last_write_time(filePath);
		auto t = mt.time_since_epoch();
		auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(t);
		std::ostringstream oss;
		oss << ms.count();
		return oss.str();
	}

	std::vector<std::string> getVideoDevicePaths(const std::string &pattern) {
		glob_t glob_result;
		memset(&glob_result, 0, sizeof(glob_result));

		int return_value = glob(pattern.c_str(), GLOB_TILDE, NULL, &glob_result);
		if (return_value != 0) {
			globfree(&glob_result);
			std::ostringstream ss;
			ss << "glob() failed with return_value " << return_value << std::endl;
			throw std::runtime_error(ss.str());
		}

		std::vector<std::string> filenames;
		for (size_t i = 0; i < glob_result.gl_pathc; ++i) {
			filenames.push_back(std::string(glob_result.gl_pathv[i]));
		}

		globfree(&glob_result);
		return filenames;
	}

// NOTE: uses by-value result
	VDevSerial getVideoDeviceSerial(bool verbose, const std::string &devPath) {
		VDevSerial vdi;
		std::string cmd = "v4l2-ctl -d " + devPath + " --info";

		//std::string res = exec_cmd(verbose, cmd);
		std::string res = exec(verbose, cmd);
		//_INFO("Result: " << res);
		std::regex reVideoCapture("Video Capture");

		// Find "Device Caps" section
		std::size_t pos1 = res.find("Device Caps");
		if (pos1 != std::string::npos) {
			res = res.substr(pos1);

			// Find "Video Capture" line in remaining text
			std::size_t pos2 = res.find("Video Capture");
			if (pos2 != std::string::npos) {
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
	VDevPath getVideoDevicePathBySerial(bool verbose, const std::string &pattern, const std::string &serial) {
		VDevPath res;
		// NOTE: ?? should we use "v4l2-ctl --list-devices | grep /dev" to determine possible devices
		std::vector<std::string> v1 = getVideoDevicePaths(pattern);

		for (const auto &path: v1) {
			_VERBOSE(path);
			VDevSerial vdi = getVideoDeviceSerial(verbose, path);
			if (!vdi.serialNumber.empty() && vdi.serialNumber == serial) {
				_VERBOSE("Found video device path: " << path << ", S/N=" << serial);
				res.path = path;
				res.busInfo = vdi.busInfo;
				break;
			}
		}
		return res;
	}

	std::string getTimeStr() {
		// Use chrono for high resolution time
		auto now = std::chrono::system_clock::now();
		auto nowAsTimeT = std::chrono::system_clock::to_time_t(now);
		auto nowMs = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) %
					 1000; // extract milliseconds

		// Convert to local time
		tm *ltm = localtime(&nowAsTimeT);

		// Prepare the string stream for formatting
		std::stringstream ss;
		ss << 1900 + ltm->tm_year << '.'
		   << std::setw(2) << std::setfill('0') << 1 + ltm->tm_mon << '.'
		   << std::setw(2) << std::setfill('0') << ltm->tm_mday << '.'
		   << std::setw(2) << std::setfill('0') << ltm->tm_hour << '.'
		   << std::setw(2) << std::setfill('0') << ltm->tm_min << '.'
		   << std::setw(2) << std::setfill('0') << ltm->tm_sec << '.'
		   << std::setw(3) << std::setfill('0') << nowMs.count();  // add milliseconds

		return ss.str();
	}

	bool isSysBreakExec() {
		return s_nSysBreakExec == 0 ? false : true;
	}

	std::string mwcSdkVersion() {
		BYTE bMajor = 0;
		BYTE bMinor = 0;
		WORD wBuild = 0;

		if (MWGetVersion(&bMajor, &bMinor, &wBuild) == MW_SUCCEEDED) {
			std::ostringstream ostm;
			ostm << int(bMajor) << "." << int(bMinor) << "." << int(wBuild);
			return ostm.str();
		}
		return "?.?.?";
	}

	void safeMWCloseChannel(HCHANNEL&hChannel) {
		if (hChannel != NULL) {
			MWCloseChannel(hChannel);
			hChannel = NULL;
		}
	}

	void setSysBreakExec(bool fBreak) {
		s_nSysBreakExec = fBreak ? 1 : 0;
	}

	std::string vdToString(VideoDevice &vd) {
		std::ostringstream s;
		s << vd.name << ", S/N=" << vd.serial << ", channelIndex=" << vd.channelIndex;
		return s.str();
	}

// Video signal status helpers
	std::string vssFrameRate(const MWCAP_VIDEO_SIGNAL_STATUS &vss) {
		char frameRate[256] = {0};
		sprintf(frameRate, "%.0f", round(10000000. / (vss.dwFrameDuration == 0 ? -1 : vss.dwFrameDuration)));
		return frameRate;
	}

	bool vssEquals(const MWCAP_VIDEO_SIGNAL_STATUS &vss1,
				   const MWCAP_VIDEO_SIGNAL_STATUS &vss2) {
		// TODO: ?? structure has also x and y fields, but it isn't used in
		// original code, should we check it as well ??
		return
				(vss1.state == vss2.state) &&
				(vss1.cx == vss2.cx) &&
				(vss1.cy == vss2.cy) &&
				(vss1.cxTotal == vss2.cxTotal) &&
				(vss1.cyTotal == vss2.cyTotal) &&
				(vss1.bInterlaced == vss2.bInterlaced) &&
				(vss1.dwFrameDuration == vss2.dwFrameDuration) &&
				(vss1.nAspectX == vss2.nAspectX) &&
				(vss1.nAspectY == vss2.nAspectY) &&
				(vss1.bSegmentedFrame == vss2.bSegmentedFrame) &&
				(vss1.frameType == vss2.frameType) &&
				(vss1.colorFormat == vss2.colorFormat) &&
				(vss1.quantRange == vss2.quantRange) &&
				(vss1.satRange == vss2.satRange);
	}

	std::string vssToString(const MWCAP_VIDEO_SIGNAL_STATUS &vsStatus) {
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
} // reprostim