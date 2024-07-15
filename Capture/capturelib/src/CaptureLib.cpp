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
#include "reprostim/CaptureLib.h"


namespace fs = std::filesystem;

namespace reprostim {

	// private static global flag
	static volatile sig_atomic_t s_nSysBreakExec = 0;

	static std::unordered_map<std::string, std::string> s_audioInAliasNameMap = {
			{"line-in", "Line In Capture Volume"},
			{"linein", "Line In Capture Volume"},
			{"hdmi", "HDMI Capture Volume"}
	};

	bool checkOutDir(const std::string &outDir) {
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

	int checkSystem() {
		// check ffmpeg
		std::string ffmpeg = exec("which ffmpeg");
		if (ffmpeg.empty()) {
			_ERROR("ffmpeg program not found. Please make sure ffmpeg package is installed.");
			return EX_UNAVAILABLE;
		}

		// check v4l2-ctl
		std::string v4l2ctl = exec("which v4l2-ctl");
		if (v4l2ctl.empty()) {
			_ERROR("v4l2-ctl program not found. Please make sure v4l-utils package is installed.");
			return EX_UNAVAILABLE;
		}

		return EX_OK;
	}

	std::string chiToString(const MWCAP_CHANNEL_INFO &info) {
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

	std::string exec(const std::string &cmd,
					 bool showStdout,
					 int maxResLen,
					 std::function<bool()> isTerminated
					 ) {
		std::array<char, 128> buffer;
		std::string result;
		std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
		if (!pipe) {
			_ERROR("popen() failed for cmd: " << cmd);
			throw std::runtime_error("popen() failed!");
		}
		while (!isTerminated() && fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
			if( !(maxResLen>0 && result.size()>=maxResLen) ) {
				result += buffer.data();
			}
			if (showStdout) {
				_INFO_RAW(buffer.data());
				fflush(stdout); // force output
			}
		}

		if( maxResLen>0 && result.size()>=maxResLen ) {
			result += " ...";
		}

		_VERBOSE("exec -> :  " << result);
		return result;
	}

	// Expand macros like {key} or ${key} in text using dict
	std::string expandMacros(const std::string &text, const SDict &dict) {
		std::string s = text;
		std::regex re(R"(\$?\{(\w+)\})");
		std::smatch m;

		int n = 0;
		while (std::regex_search(s, m, re)) {
			auto key = m[1].str();
			auto it = dict.find(key);
			if (it != dict.end()) {
				s = m.prefix().str() + it->second + m.suffix().str();
				//result.replace(matches.position(), matches.length(), it->second);
			} else {
				// Handle missing parameter error
				_ERROR("Invalid macros parameter: " << key << " in " << text);
				s = m.prefix().str() + "?" + key + "?" + m.suffix().str();
				//s.replace(m.position(), m.length(), "?" + paramName + "?");
			}
			if( n++ > 28 ) {
				_ERROR("Too many macros replacements, possible infinite loop: " << n);
				break;
			}
		}
		return s;
	}

	bool findTargetVideoDevice(const std::string &serialNumber,
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

			_VERBOSE("Found device on channel " << i << ". " << info);

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

	// get audio-in control name by reprostim alias
	std::string getAudioInNameByAlias(const std::string &alias) {
		std::string res;
		auto it = s_audioInAliasNameMap.find(alias);
		if (it != s_audioInAliasNameMap.end()) {
			res = it->second;
		}
		return res;
	}

	AudioInDevice getAudioInDevice(const std::string &busInfo,
								   const std::string &device) {
		AudioInDevice res;

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
						ostm << "hw:" << std::to_string(card);
						std::string alsaCardName = ostm.str();
						ostm << "," ;

						std::string deviceId = device;
						if( deviceId.empty() ) {
							deviceId = getDefaultAudioInDeviceByCard(alsaCardName);
						}
						ostm << deviceId;

						res.alsaCardName = alsaCardName;
						res.alsaDeviceName = ostm.str();
						res.cardId = std::to_string(card);
						res.deviceId = deviceId;
						break;
					}
				}

			}
		} while (snd_card_next(&card) >= 0 && card >= 0);
		return res;
	}

	static std::string getAudioCtlElemName(snd_ctl_elem_id_t *id)
	{
		std::string res;
		char *str;
		str = snd_ctl_ascii_elem_id_get(id);
		if (str) {
			res = str;
			//_VERBOSE("getAudioCtlElemName=" << str);
			free(str);
		}
		return res;
	}

	std::string getDefaultAudioInDeviceByCard(const std::string &alsaCardName) {
		std::string res = DEFAULT_AUDIO_IN_DEVICE;

		int err = 0 ;
		snd_hctl_t *handle;
		snd_hctl_elem_t *elem;
		snd_ctl_elem_id_t *id;
		snd_ctl_elem_info_t *info;
		snd_ctl_elem_id_alloca(&id);
		snd_ctl_elem_info_alloca(&info);

		if( (err = snd_hctl_open(&handle, alsaCardName.c_str(), 0)) < 0 ) {
			_ERROR("Failed snd_hctl_open: " << alsaCardName << ", " << snd_strerror(err));
			return res;
		}

		if( (err = snd_hctl_load(handle)) < 0 ) {
			_ERROR("Failed snd_hctl_load: " << alsaCardName << ", " << snd_strerror(err));
			snd_hctl_close(handle);
			return res;
		}

		for( elem = snd_hctl_first_elem(handle); elem; elem = snd_hctl_elem_next(elem) ) {
			if ((err = snd_hctl_elem_info(elem, info)) < 0) {
				_ERROR("Failed snd_hctl_elem_info: " << alsaCardName << ", " << snd_strerror(err));
				break;
			}
			snd_hctl_elem_get_id(elem, id);
			std::string elemName = getAudioCtlElemName(id);
			_VERBOSE("HCTL Elem (card="<< alsaCardName << ") : " << elemName);
			// try to find string in format like listed below and locate device there:
			// numid=4,iface=PCM,name='Capture Channel Map',device=1
			int pos = 0;
			if( elemName.find("iface=PCM") != std::string::npos &&
				elemName.find("Capture Channel Map") != std::string::npos &&
				(pos = elemName.find("device=")) != std::string::npos ) {
				res = elemName.substr(pos+7);
				if( res.empty() ) {
					res = DEFAULT_AUDIO_IN_DEVICE;
				} else {
					_VERBOSE("Found audio-in ALSA device : " << res);
					break;
				}
			}
		}
		snd_hctl_close(handle);
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
	VDevSerial getVideoDeviceSerial(const std::string &devPath) {
		VDevSerial vdi;
		std::string cmd = "v4l2-ctl -d " + devPath + " --info";

		//std::string res = exec_cmd(verbose, cmd);
		std::string res = exec(cmd);
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
	VDevPath getVideoDevicePathBySerial(const std::string &pattern, const std::string &serial) {
		VDevPath res;
		// NOTE: ?? should we use "v4l2-ctl --list-devices | grep /dev" to determine possible devices
		std::vector<std::string> v1 = getVideoDevicePaths(pattern);

		for (const auto &path: v1) {
			_VERBOSE(path);
			VDevSerial vdi = getVideoDeviceSerial(path);
			if (!vdi.serialNumber.empty() && vdi.serialNumber == serial) {
				_VERBOSE("Found video device path: " << path << ", S/N=" << serial);
				res.path = path;
				res.busInfo = vdi.busInfo;
				break;
			}
		}
		return res;
	}

	std::string getTimeStr(const Timestamp &ts) {
		auto tsAsTimeT = std::chrono::system_clock::to_time_t(ts);
		auto tsAsMs = std::chrono::duration_cast<std::chrono::milliseconds>(ts.time_since_epoch()) %
					  1000; // extract milliseconds

		// Convert to local time
		tm *ltm = localtime(&tsAsTimeT);

		// Prepare the string stream for formatting
		std::stringstream ss;
		ss << 1900 + ltm->tm_year << '.'
		   << std::setw(2) << std::setfill('0') << std::to_string(1 + ltm->tm_mon) << '.'
		   << std::setw(2) << std::setfill('0') << std::to_string(ltm->tm_mday) << '-'
		   << std::setw(2) << std::setfill('0') << std::to_string(ltm->tm_hour) << '.'
		   << std::setw(2) << std::setfill('0') << std::to_string(ltm->tm_min) << '.'
		   << std::setw(2) << std::setfill('0') << std::to_string(ltm->tm_sec) << '.'
		   << std::setw(3) << std::setfill('0') << std::to_string(tsAsMs.count());  // add milliseconds

		return ss.str();
	}

	std::string getTimeFormatStr(const Timestamp &ts,
								 const std::string &format) {
		auto tsAsTimeT = std::chrono::system_clock::to_time_t(ts);
		std::stringstream ss;
		ss << std::put_time(std::localtime(&tsAsTimeT), format.c_str());
		return ss.str();
	}

	// ISO 8601 date-time string conversion
	std::string getTimeIsoStr(const Timestamp &ts) {
		std::stringstream ss;
		ss << getTimeFormatStr(ts, "%Y-%m-%dT%H:%M:%S");

		// put also microseconds up to 6 digits
		auto nowUs = std::chrono::duration_cast<std::chrono::microseconds>(ts.time_since_epoch()) % 1000000;
		ss << '.' << std::setw(6) << std::setfill('0') << nowUs.count();
		return ss.str();
	}

	bool isSysBreakExec() {
		return s_nSysBreakExec == 0 ? false : true;
	}

	static void listAudioControls(const std::string &cardName,
								  const std::string &indent)
	{
		int err = 0 ;
		snd_hctl_t *handle;
		snd_hctl_elem_t *elem;
		snd_ctl_elem_id_t *id;
		snd_ctl_elem_info_t *info;
		snd_ctl_elem_value_t *control;
		snd_ctl_elem_id_alloca(&id);
		snd_ctl_elem_info_alloca(&info);
		snd_ctl_elem_value_alloca(&control);

		if( (err = snd_hctl_open(&handle, cardName.c_str(), 0)) < 0 ) {
			_ERROR("Failed snd_hctl_open: " << cardName << ", " << snd_strerror(err));
			return;
		}

		if( (err = snd_hctl_load(handle)) < 0 ) {
			_ERROR("Failed snd_hctl_load: " << cardName << ", " << snd_strerror(err));
			snd_hctl_close(handle);
			return;
		}

		int j = 0;
		for( elem = snd_hctl_first_elem(handle); elem; elem = snd_hctl_elem_next(elem) ) {
			if ((err = snd_hctl_elem_info(elem, info)) < 0) {
				_ERROR("Failed snd_hctl_elem_info: " << cardName << ", " << snd_strerror(err));
				break;
			}
			_VERBOSE("elem: info=" << info);
			//if( snd_ctl_elem_info_is_inactive(info) )
			//	continue;
			snd_hctl_elem_get_id(elem, id);
			_VERBOSE("elem: id=" << id);
			std::string sElem = getAudioCtlElemName(id);
			_INFO(indent << "HCTL Elem[" << std::to_string(j) << "] : " << sElem);
			if( sElem.find("iface=MIXER") != std::string::npos &&
				sElem.find("Capture Volume") != std::string::npos ) {
				long nVolMin = snd_ctl_elem_info_get_min(info);
				long nVolMax = snd_ctl_elem_info_get_max(info);
				long nVol = -1;
				// read current value
				snd_ctl_elem_value_set_id(control, id);
				if ((err = snd_hctl_elem_read(elem, control)) < 0) {
					_ERROR("Failed snd_hctl_elem_read: " << cardName << ", " << snd_strerror(err));
				} else {
					nVol = snd_ctl_elem_value_get_integer(control, 0);
					//long l = snd_ctl_ascii_value_parse(handle, control, info, "80%");
					//snd_ctl_elem_value_set_integer(control, 0, (nVol+1));
					//if ((err = snd_hctl_elem_write(elem, control)) < 0) {
					//	_ERROR("Failed snd_hctl_elem_write: " << cardName << ", " << snd_strerror(err));
					//}
				}
				_INFO(indent << "             : volume(min=" << std::to_string(nVolMin)
							<< ", max=" << std::to_string(nVolMax)
							<< ", current=" << std::to_string(nVol) << ")"
				);
				for( const auto& entry : s_audioInAliasNameMap ) {
					if( sElem.find(entry.second) != std::string::npos ) {
						_INFO(indent << "             : reprostim alias=" << entry.first);
					}
				}
			}

			//unsigned int count = snd_ctl_elem_info_get_count(info);
			//snd_ctl_elem_type_t type_ = snd_ctl_elem_info_get_type(info);
			//_INFO("count=" << count << ", type=" << type_);
			j++;
		}
		snd_hctl_close(handle);

		getDefaultAudioInDeviceByCard(cardName);
		return;
	}


	void listAudioDevices() {
		snd_pcm_stream_t stream = SND_PCM_STREAM_CAPTURE; // SND_PCM_STREAM_PLAYBACK;
		//
		snd_ctl_t *handle;
		snd_ctl_card_info_t *info;
		snd_pcm_info_t *pcminfo;
		// stack memory
		snd_ctl_card_info_alloca(&info);
		snd_pcm_info_alloca(&pcminfo);

		int card = -1;

		if (snd_card_next(&card) < 0 || card < 0) {
			return;
		}

		_INFO("Stream: " << snd_pcm_stream_name(stream));

		do {
			std::string cardAlsaName = "hw:" + std::to_string(card);
			if (snd_ctl_open(&handle, cardAlsaName.c_str(), 0) < 0) {
				_ERROR("Cannot open control for card" << card);
				continue;
			}

			if (snd_ctl_card_info(handle, info) >= 0) {
				std::string id = snd_ctl_card_info_get_id(info);
				std::string name = snd_ctl_card_info_get_name(info);
				std::string lname = snd_ctl_card_info_get_longname(info);
				_INFO("  Sound Card " << std::to_string(int(card)) << ":");
				_INFO("    ALSA Name : " << cardAlsaName);
				_INFO("    ID        : " << id);
				_INFO("    Name      : " << name);
				_INFO("    LName     : " << lname);
				_INFO("    Devices   :");

				int dev = -1;
				int err = 0;

				while( true ) {
					unsigned int count = 0;
					if( snd_ctl_pcm_next_device(handle, &dev)<0 ) {
						_ERROR("Failed snd_ctl_pcm_next_device");
					}

					if( dev<0 ) {
						break;
					}

					snd_pcm_info_set_device(pcminfo, dev);
					snd_pcm_info_set_subdevice(pcminfo, 0);
					snd_pcm_info_set_stream(pcminfo, stream);
					if ((err = snd_ctl_pcm_info(handle, pcminfo)) < 0) {
						if (err != -ENOENT)
							_ERROR("Failed snd_ctl_pcm_info: " << snd_strerror(err));
						continue;
					}
					_INFO("      Device " << std::to_string(dev) << ":");
					_INFO("        ALSA Name : " << cardAlsaName << "," << std::to_string(dev));
					_INFO("        ID        : " << snd_pcm_info_get_id(pcminfo));
					_INFO("        Name      : " << snd_pcm_info_get_name(pcminfo));

					int c = snd_pcm_info_get_subdevices_count(pcminfo);
					_INFO("        Subdevices: ");
					_INFO("          Count: " << c);
					_INFO("          Avail: " << snd_pcm_info_get_subdevices_avail(pcminfo));

					for( int i=0; i<c; i++) {
						snd_pcm_info_set_subdevice(pcminfo, i);
						if ((err = snd_ctl_pcm_info(handle, pcminfo)) < 0) {
							_ERROR("Failed  snd_ctl_pcm_info: " << snd_strerror(err));
						} else {
							_INFO("          Subdevice " << std::to_string(i) << ":");
							_INFO("            Name : " << snd_pcm_info_get_subdevice_name(pcminfo));
						}
					}
				}
				snd_ctl_close(handle);
				_INFO("    Controls  :");
				listAudioControls(cardAlsaName, "      ");
			}
		} while (snd_card_next(&card) >= 0 && card >= 0);
	}

	void listVideoDevices() {
		_VERBOSE("listVideoDevices()")
		const int MAX_CAPTURE = 16;
		MW_RESULT mr = MW_SUCCEEDED;

		BOOL fInit = MWCaptureInitInstance();
		if( !fInit )
			_ERROR("Failed MWCaptureInitInstance");

		for(int k = 0; k<1; k++) {
			SLEEP_MS(1);
			mr = MWRefreshDevice();
			if (mr != MW_SUCCEEDED)
			_ERROR("Failed MWRefreshDevice: " << mr);

			int n = MWGetChannelCount();
			MWCAP_CHANNEL_INFO mci;
			MWCAP_VIDEO_SIGNAL_STATUS vss;

			for (int i = 0; i < n; i++) {
				mr = MWGetChannelInfoByIndex(i, &mci);
				if (mr != MW_SUCCEEDED) {
					_ERROR("Failed MWGetChannelInfoByIndex[" << std::to_string(i) << "]: " << mr);
					continue;
				}
				_INFO("Channel [" << std::to_string(i) << "]: " << mci);

				char wPath[256] = {0};
				if (MWGetDevicePath(i, wPath) == MW_SUCCEEDED) {
					_INFO("  Device instance path: " << wPath);
				} else {
					_ERROR("Failed MWGetDevicePath[" << std::to_string(i) << "]");
					continue;
				}

				HCHANNEL hChannel = MWOpenChannelByPath(wPath);
				if (hChannel == NULL) {
					_ERROR("Failed MWOpenChannelByPath[" << std::to_string(i) << "]");
					continue;
				}

				MWGetChannelInfo(hChannel, &mci);
				_INFO("Channel [" << std::to_string(i) << "]: " << mci);

				MWGetVideoSignalStatus(hChannel, &vss);
				_INFO("  Video Signal Status: " << vss);

				safeMWCloseChannel(hChannel);

				if (i >= MAX_CAPTURE) {
					_ERROR("Max capture limit reached: " << std::to_string(MAX_CAPTURE));
					break;
				}
			}
		}

		MWCaptureExitInstance();
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

 	AudioVolume parseAudioVolume(const std::string text) {
		std::string sVol = text;
		AudioVolume av;
		av.unit = VolumeLevelUnit::RAW;
		av.label = sVol;
		if(sVol.empty()) {
			throw std::runtime_error("empty text");
		}

		if(sVol.ends_with('%') && sVol.length() > 1 ) {
			sVol = sVol.substr(0, sVol.length() - 1);
			av.unit = VolumeLevelUnit::PERCENT;
		}

		if((sVol.ends_with("db") || sVol.ends_with("dB")) && sVol.length() > 2 ) {
			sVol = sVol.substr(0, sVol.length() - 2);
			av.unit = VolumeLevelUnit::DB;
		}

		size_t pos = 0;
		av.level = std::stof(sVol, &pos);
		if(pos < sVol.length() ) {
			throw std::runtime_error("Usupported volume level value "+av.label);
		}

		if(av.unit == VolumeLevelUnit::PERCENT ) {
			if( av.level<0.0 ) {
				throw std::runtime_error("Invalid percent value "+av.label);
			} else
			if( av.level>100.0 ) {
				throw std::runtime_error("Invalid percent value "+av.label);
			}
		}
		return av;
	}


	void safeMWCloseChannel(HCHANNEL&hChannel) {
		if (hChannel != NULL) {
			MWCloseChannel(hChannel);
			hChannel = NULL;
		}
	}

	void setAudioInVolumeByCard(const std::string &cardName,
								const std::unordered_map<std::string, AudioVolume> &mapNameVolume)
	{
		_VERBOSE("setAudioInVolumeByCard: card=" << cardName << ", mapNameVolume.size=" << mapNameVolume. size());
		int err = 0 ;
		snd_hctl_t *handle;
		snd_hctl_elem_t *elem;
		snd_ctl_elem_id_t *id;
		snd_ctl_elem_info_t *info;
		snd_ctl_elem_value_t *control;
		snd_ctl_elem_id_alloca(&id);
		snd_ctl_elem_info_alloca(&info);
		snd_ctl_elem_value_alloca(&control);

		if( (err = snd_hctl_open(&handle, cardName.c_str(), 0)) < 0 ) {
			_ERROR("Failed setAudioInVolumeByCard, snd_hctl_open: " << cardName << ", " << snd_strerror(err));
			return;
		}

		if( (err = snd_hctl_load(handle)) < 0 ) {
			_ERROR("Failed setAudioInVolumeByCard, snd_hctl_load: " << cardName << ", " << snd_strerror(err));
			snd_hctl_close(handle);
			return;
		}

		int j = 0;
		for( elem = snd_hctl_first_elem(handle); elem; elem = snd_hctl_elem_next(elem) ) {
			if ((err = snd_hctl_elem_info(elem, info)) < 0) {
				_ERROR("Failed setAudioInVolumeByCard, snd_hctl_elem_info: " << cardName << ", " << snd_strerror(err));
				break;
			}
			_VERBOSE("elem: info=" << info);
			//if( snd_ctl_elem_info_is_inactive(info) )
			//	continue;
			snd_hctl_elem_get_id(elem, id);
			std::string sElem = getAudioCtlElemName(id);
			_VERBOSE("elem: id=" << id << ", "  << sElem);
			if( sElem.find("iface=MIXER") != std::string::npos ) {
				for( const auto& entry : mapNameVolume) {
					std::string controlName = getAudioInNameByAlias(entry.first);
					if( !controlName.empty() && sElem.find(controlName) != std::string::npos ) {
						long nVolMin = snd_ctl_elem_info_get_min(info);
						long nVolMax = snd_ctl_elem_info_get_max(info);
						long nVol = -1;
						// read current value
						snd_ctl_elem_value_set_id(control, id);
						if ((err = snd_hctl_elem_read(elem, control)) < 0) {
							_ERROR("Failed setAudioInVolumeByCard, snd_hctl_elem_read: " << cardName << ", "
																						 << snd_strerror(err));
						} else {
							nVol = snd_ctl_elem_value_get_integer(control, 0);
							_VERBOSE("Audio-In HCTL: " << sElem << ", Volume(min=" << std::to_string(nVolMin)
													<< ", max=" << std::to_string(nVolMax)
													<< ", current=" << std::to_string(nVol) << ")"
							);

							// set HCTL volume specified on AudioVolume
							const AudioVolume& av = entry.second;
							long nVol2 = nVol;
							if(av.unit == VolumeLevelUnit::PERCENT ) {
								nVol2 = static_cast<long>(nVolMin + std::round(((nVolMax - nVolMin) * av.level) / 100.0));
								if( nVol2<nVolMin ) {
									nVol2 = nVolMin;
								}
								if( nVol2>nVolMax ) {
									nVol2 = nVolMax;
								}
							} else if(av.unit == VolumeLevelUnit::RAW ) {
								nVol2 = av.getLevelAsLong();
							} else {
								_ERROR("Unsupported volume unit: " << av.unit << ", " << av.label);
							}

							if( nVol2 != nVol ) {
								if( nVol2>=nVolMin && nVol2<=nVolMax) {
									_INFO("Set audio-in device volume, {"
										<< sElem
										<< "}, alias=" << entry.first
										<< ", level(min=" << std::to_string(nVolMin)
										<< ", max=" << std::to_string(nVolMax)
										<< ", old=" << std::to_string(nVol)
										<< ", new=" << std::to_string(nVol2)
										<< ", label=" << av.label
										<< ")"
									);
									_INFO("Set volume for Left channel: " << nVol2);
									snd_ctl_elem_value_set_integer(control, 0, nVol2);
									if ((err = snd_hctl_elem_write(elem, control)) < 0) {
										_ERROR("Failed setAudioInVolumeByCard, snd_hctl_elem_write: " << cardName
																									  << ", 0, "
																									  << snd_strerror(
																											  err));
									}
									_INFO("Set volume for Right channel: " << nVol2);
									snd_ctl_elem_value_set_integer(control, 1, nVol2);
									if ((err = snd_hctl_elem_write(elem, control)) < 0) {
										_ERROR("Failed setAudioInVolumeByCard, snd_hctl_elem_write: " << cardName
																									  << ", 1, "
																									  << snd_strerror(
																											  err));
									}
								} else {
									_ERROR("Invalid audio-in volume level: " << nVol2
										<< ", {" << sElem
										<< "}, alias=" << entry.first
										<< ", level(min=" << std::to_string(nVolMin)
										<< ", max=" << std::to_string(nVolMax)
										<< ", cur=" << std::to_string(nVol)
										<< ")"
									);
								}
							}
						}
					}
				}
			}
			j++;
		}
		snd_hctl_close(handle);
	}

	void setSysBreakExec(bool fBreak) {
		s_nSysBreakExec = fBreak ? 1 : 0;
	}

	std::string vdToString(const VideoDevice &vd) {
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
