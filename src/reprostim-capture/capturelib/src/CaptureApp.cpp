#include <iostream>
#include <sstream>
#include <chrono>
#include <csignal>
#include <thread>
#include <sysexits.h>
#include "reprostim/CaptureApp.h"

namespace reprostim {

	int checkConduct(const ConductOpts& opts) {
		if (!opts.enabled) {
			_VERBOSE("Conduct monitoring is disabled");
			return EX_OK;
		}
		std::string cmd = opts.duct_bin + " --version";
		std::string res = exec(cmd);
		if (res.empty() || !res.starts_with("duct ")) {
			_ERROR("con/duct utility not found. Please make sure it's installed with 'pip install con-duct'");
			_ERROR("  and configured correctly in config.yaml -> conduct_opts -> duct_bin .");
			_ERROR("  COMMAND : " << cmd);
			_ERROR("  RESULT  : " << res);
			return EX_UNAVAILABLE;
		}
		_VERBOSE("con/duct utility found: " << res);
		return EX_OK;
	}

	uint32_t fnv1_32(const std::string& s) {
		const uint32_t prime = 16777619u;
		uint32_t hash = 2166136261u; // offset basis

		for (unsigned char c : s) {
			hash ^= c;
			hash *= prime;
		}
		return hash;
	}

	std::string toHex8(uint32_t value) {
		std::ostringstream oss;
		oss << std::hex << std::setfill('0') << std::setw(8) << value;
		return oss.str();
	}

	void signalHandler(int signum) {
		//_INFO("Signal received: " << signum);
		if (signum == SIGINT) {
			_INFO("Ctrl+C received. Terminating...");
			if(isSysBreakExec() ) {
				_INFO("Force exit, 2nd attempt");
				std::exit(signum);
			}
			setSysBreakExec(true);
		}
		if( signum == SIGTERM  || signum == SIGKILL ) {
			_INFO("Termination or kill: " << signum);
			if(isSysBreakExec() ) {
				_INFO("Force exit, 2nd attempt");
				std::exit(signum);
			}
			setSysBreakExec(true);
		}
	}

	CaptureApp::CaptureApp() {
		appName = "TODO_appName";
		audioEnabled = true;
	}

	CaptureApp::~CaptureApp() {
		if( pRepromonQueue ) {
			pRepromonQueue->stop();
		}
		pRepromonQueue = nullptr;
		unregisterFileLogger(_FILE_LOGGER_NAME);
		setLogPattern(LogPattern::SIMPLE);
	}

	std::string CaptureApp::createOutPath(const std::optional<Timestamp> &ts, bool fCreateDir) {
		const Timestamp &ts2 = ts.value_or(tsStart);

		std::string s = expandMacros(
				opts.outPathTempl,
				{
					{"year",  getTimeYearStr(ts2)  },
					{"month", getTimeMonthStr(ts2) }
				});

		_VERBOSE("Expanded out path template: " << s);

		if( fCreateDir ) {
			_VERBOSE("Create output path: " << s);
			if( !checkOutDir(s) ) {
				_ERROR("ERROR[009]: Failed create output path: " << opts.outPathTempl << " -> " << s);
			}
		}
		return s;
	}

	SessionLogger_ptr CaptureApp::createSessionLogger(const std::string& name, const std::string& filePath) {
		if( cfg.session_logger_enabled ) {
			SessionLogger_ptr pLogger = std::make_shared<FileLogger>();
			pLogger->open(name,
						  filePath,
						  cfg.session_logger_level,
						  cfg.session_logger_pattern);
			std::string ver = appName + " " + CAPTURE_VERSION_STRING;
			pLogger->info("Session logging begin   : " + ver + ", " + name
						  + ", start_ts=" + start_ts);
			pLogger->info("        Video device    : " + targetVideoDevPath +
				", S/N: " + targetVideoDev.serial + ", " + targetVideoDev.name +
				", bus info: " + targetBusInfo);
			pLogger->info("                        : " + std::to_string(vssCur.cx) + "x" +
						  std::to_string(vssCur.cy) + ", " + frameRate + " fps");
			if( audioEnabled ) {
				pLogger->info("        Audio-in device : " + targetAudioInDevPath);
				for(const auto& entry: cfg.ffm_opts.a_vol) {
					pLogger->info("                        : " + entry.first +
						+ "/" + getAudioInNameByAlias(entry.first) +
						"=" + entry.second.label
					);
				}
			}
			return pLogger;
		}
		return nullptr;
	}

	void CaptureApp::listDevices(const std::string& devices) {
		printVersion();
		if( !(devices == "all" || devices == "audio" || devices == "video") ) {
			_ERROR("Invalid device type: " << devices << ", must be 'all', 'audio' or 'video'");
			return;
		}
		if( devices=="all" || devices=="video" ) {
			_INFO(" ");
			_INFO("[List of available Video devices]:");
			listVideoDevices();
		}
		if( devices=="all" || devices=="audio" ) {
			_INFO(" ");
			_INFO("[List of available Audio devices]:");
			if (audioEnabled) {
				listAudioDevices();
			} else {
				_INFO("Audio capture is disabled in " << appName);
			}
		}
	}

	bool CaptureApp::loadConfig(AppConfig& cfg, const std::string& pathConfig) {
		YAML::Node doc;
		try {
			doc = YAML::LoadFile(pathConfig);
		} catch(const std::exception& e) {
			_ERROR("ERROR[008]: Failed load/parse config file "
						   << pathConfig << ": " << e.what());
			return false;
		}

		if( doc["device_serial_number"] ) {
			cfg.device_serial_number = getYamlProp<std::string>(doc, "device_serial_number");
			cfg.has_device_serial_number = !cfg.device_serial_number.empty() &&
										   cfg.device_serial_number!="auto";
		} else {
			cfg.has_device_serial_number = false;
		}

		if( doc["video_device_path_pattern"] ) {
			cfg.video_device_path_pattern = getYamlProp<std::string>(doc, "video_device_path_pattern");
		}

		if( doc["instance_tag"] ) {
			cfg.instance_tag = getYamlProp<std::string>(doc, "instance_tag");
			cfg.has_instance_tag = !cfg.instance_tag.empty() && cfg.instance_tag!="auto";
		} else {
			cfg.has_instance_tag = false;
		}

		if( doc["session_logger_enabled"] ) {
			cfg.session_logger_enabled = getYamlProp<bool>(doc, "session_logger_enabled");
			cfg.session_logger_level = parseLogLevel(getYamlProp<std::string>(doc, "session_logger_level"));
			cfg.session_logger_pattern = getYamlProp<std::string>(doc, "session_logger_pattern");
		}

		if( doc["ffm_opts"] ) {
			YAML::Node node = doc["ffm_opts"];
			FfmpegOpts& opts = cfg.ffm_opts;
			opts.a_fmt = getYamlProp<std::string>(node, "a_fmt");
			opts.a_nchan = getYamlProp<std::string>(node, "a_nchan");
			opts.a_opt = getYamlProp<std::string>(node, "a_opt");
			opts.a_dev = getYamlProp<std::string>(node, "a_dev");
			opts.has_a_dev = !opts.a_dev.empty() && opts.a_dev.find("auto")==std::string::npos;
			opts.a_alsa_dev = DEFAULT_AUDIO_IN_DEVICE;
			opts.has_a_alsa_dev = false;
			if( opts.a_dev.find("auto,")==0 ) {
				std::string alsaDev = opts.a_dev.substr(5);
				if( !alsaDev.empty() ) {
					opts.a_alsa_dev = alsaDev;
					opts.has_a_alsa_dev = true;
				}
			}

			// parse a_vol
			if( node["a_vol"] ) {
				YAML::Node nodeVol = node["a_vol"];
				for(YAML::const_iterator it=nodeVol.begin(); it!=nodeVol.end(); ++it) {
					std::string key = it->first.as<std::string>();
					std::string audioName = getAudioInNameByAlias(key);
					if( audioName.empty() ) {
						_ERROR("Failed parse audio volume: " << key << ", unknown audio device alias");
						return false;
					}
					YAML::Node nodeVol2 = nodeVol[key];
					try {
						opts.a_vol[key] = parseAudioVolume(nodeVol2.as<std::string>());
					} catch (const std::exception& e) {
						_ERROR("Failed parse audio volume: " << key << ", " << e.what());
						return false;
					}
				}
			}
			opts.v_fmt = getYamlProp<std::string>(node, "v_fmt");
			opts.v_opt = getYamlProp<std::string>(node, "v_opt");
			opts.v_dev = getYamlProp<std::string>(node, "v_dev");
			opts.v_enc = getYamlProp<std::string>(node, "v_enc");
			opts.has_v_dev = !opts.v_dev.empty() && opts.v_dev != "auto";
			opts.pix_fmt = getYamlProp<std::string>(node, "pix_fmt");
			opts.n_threads = getYamlProp<std::string>(node, "n_threads");
			opts.a_enc = getYamlProp<std::string>(node, "a_enc");
			opts.out_fmt = getYamlProp<std::string>(node, "out_fmt");
		}

		// load conduct_opts
		if( doc["conduct_opts"] ) {
			YAML::Node node = doc["conduct_opts"];
			ConductOpts& opts = cfg.conduct_opts;
			opts.enabled = getYamlProp<bool>(node, "enabled");
			opts.cmd = getYamlProp<std::string>(node, "cmd");
			opts.duct_bin = getYamlProp<std::string>(node, "duct_bin");
		}


		// load ext_proc_opts
		if( doc["ext_proc_opts"] ) {
			YAML::Node node = doc["ext_proc_opts"];
			ExtProcOpts& opts = cfg.ext_proc_opts;
			opts.enabled = getYamlProp<bool>(node, "enabled");
			opts.status_command = getYamlProp<std::string>(node, "status_command");
			opts.status_delay_ms = getYamlProp<int>(node,"status_delay_ms");
			opts.status_regex = getYamlProp<std::string>(node, "status_regex");
			opts.exec_command = getYamlProp<std::string>(node, "exec_command");
			opts.exec_restart_on_exit = getYamlProp<bool>(node,"exec_restart_on_exit");
		}

		// load repromon_opts
		if( doc["repromon_opts"] ) {
			YAML::Node node = doc["repromon_opts"];
			RepromonOpts& opts = cfg.repromon_opts;
			opts.enabled = getYamlProp<bool>(node,"enabled");
			opts.api_base_url = getYamlProp<std::string>(node, "api_base_url");
			opts.api_key = getYamlProp<std::string>(node, "api_key");
			if( opts.enabled && opts.api_key=="${REPROMON_API_KEY}" ) {
				const char* envApiKey = std::getenv("REPROMON_API_KEY");
				if( envApiKey!=nullptr ) {
					opts.api_key = envApiKey;
					_VERBOSE("Expanded repromon api_key: " << opts.api_key);
				} else {
					_ERROR("Failed expand repromon api_key in config.yaml, "
						   "env variable not found: "
						   << opts.api_key);
					return false;
				}
			}
			opts.verify_ssl_cert = getYamlProp<bool>(node, "verify_ssl_cert");
			opts.data_provider_id = getYamlProp<int>(node, "data_provider_id");
			opts.device_id = getYamlProp<int>(node,"device_id");
			opts.message_category_id = getYamlProp<int>(node, "message_category_id");
			opts.message_level_id = getYamlProp<int>(node, "message_level_id");
		}
		return this->onLoadConfig(cfg, pathConfig, doc);
	}

	void CaptureApp::onCaptureIdle() {
	}

	void CaptureApp::onCaptureStart() {
		_INFO("TODO: onCaptureStart");
	}

	void CaptureApp::onCaptureStop(const std::string& message) {
		_INFO("TODO: onCaptureStop" << message);
	}

	bool CaptureApp::onLoadConfig(AppConfig &cfg, const std::string &pathConfig, YAML::Node doc) {
		return true;
	}

	void CaptureApp::onUsbDevArrived(const std::string& devPath) {
		_INFO("Connected USB device: " << devPath);
		disconnDevRemove(devPath);
		_NOTIFY_REPROMON(
			REPROMON_INFO,
			appName + " USB device connected: " + devPath
		);
	}

	void CaptureApp::onUsbDevLeft(const std::string& devPath) {
		_INFO("Disconnected USB device: " << devPath);
		disconnDevAdd(devPath);
		_NOTIFY_REPROMON(
			REPROMON_INFO,
			appName + " USB device disconnected: " + devPath
		);
	}

	int CaptureApp::parseOpts(AppOpts& opts, int argc, char* argv[]) {
		_INFO("TODO: parseOpts");
		return EX_OK;
	}

	void CaptureApp::printVersion(bool fExpanded) {
		if( fExpanded ) {
			_INFO(appName << " " << CAPTURE_VERSION_STRING);
			_INFO(" Build Type : " << CAPTURE_BUILD_TYPE);
			_INFO(" Build Date : " << CAPTURE_VERSION_DATE);
			_INFO(" Build Tag  : " << CAPTURE_VERSION_TAG);
		} else {
			_INFO(CAPTURE_VERSION_STRING);
		}
	}

	int CaptureApp::run(int argc, char* argv[]) {

		std::signal(SIGINT,  signalHandler);
		std::signal(SIGTERM, signalHandler);
		std::signal(SIGKILL, signalHandler);

		const int res1 = parseOpts(opts, argc, argv);
		setVerbose(opts.verbose);

		if( res1==1 ) return EX_OK; // help message
		if( res1!=EX_OK ) return res1;

		_VERBOSE("Config file: " << opts.configPath);

		if( !loadConfig(cfg, opts.configPath) ) {
			// config.yaml load/parse problems
			return EX_CONFIG;
		}

		_VERBOSE("Output path template: " << opts.outPathTempl);
		// just test generic outPath
		std::string testOutPath = createOutPath(CURRENT_TIMESTAMP(), false);
		_VERBOSE("Test output path: " << testOutPath);
		if( !checkOutDir(testOutPath) ) {
			// invalid output path
			_ERROR("ERROR[009]: Failed create/locate output path: " << opts.outPathTempl << " -> " << testOutPath);
			return EX_CANTCREAT;
		}

		const int res2 = checkSystem();
		if( res2!=EX_OK ) {
			// problem with system configuration and installed packages
			return res2;
		}

		const int res3 = checkConduct(cfg.conduct_opts);
		if( res3!=EX_OK ) {
			// problem with con/duct configuration or installation
			return res3;
		}

		// start repromon queue
		if( cfg.repromon_opts.enabled ) {
			fRepromonEnabled = true;
			pRepromonQueue = std::make_unique<RepromonQueue>(RepromonParams{
				cfg.repromon_opts
			});
			_VERBOSE("Start repromon queue");
			pRepromonQueue->start();
		} else {
			fRepromonEnabled = false;
		}

		// calculated options
		configHash = getFileChangeHash(opts.configPath);

		// calculate instanceTag
		if ( cfg.has_instance_tag ) {
			instanceTag = cfg.instance_tag;
		} else {
			// instance tag not specified, calculate it based
			// on appName, device serial number and home path
			instanceTag = toHex8(fnv1_32(appName)) + "-" +
						toHex8(fnv1_32(cfg.has_device_serial_number?cfg.device_serial_number:"auto")) + "-" +
						toHex8(fnv1_32(std::filesystem::absolute(opts.homePath)));
		}


		// current video signal status
		vssCur = {};

		// previous video signal status
		vssPrev = {};

		bool fRun = true;
		bool fConfigChanged = false;
		recording = 0;

		MW_RESULT mr = MW_SUCCEEDED;

		tsInit = CURRENT_TIMESTAMP();
		init_ts = getTimeStr(tsInit);
		_INFO(init_ts << ": <><><> Starting " << appName << " " << CAPTURE_VERSION_STRING << " <><><>");
		_INFO("    <> Saving output to            ===> " << opts.outPathTempl);
		_INFO("    <> Recording from Video Device ===> " << cfg.ffm_opts.v_dev
														 << ", S/N=" << (cfg.has_device_serial_number?cfg.device_serial_number:"auto"));
		if( audioEnabled ) {
			_INFO("    <> Recording from Audio Device ===> " << cfg.ffm_opts.a_dev);
		}

		if( cfg.has_device_serial_number ) {
			_VERBOSE("Use device with specified S/N: " << cfg.device_serial_number);
		} else {
			_VERBOSE("Use any first available Magewell USB Capture device");
		}

		_INFO("    <> Instance tag                ===> " << instanceTag);

		BOOL fInit = MWCaptureInitInstance();
		if( !fInit )
			_ERROR("ERROR[005]: Failed MWCaptureInitInstance");

		_VERBOSE("MWCapture SDK version: " << mwcSdkVersion());

		// register USB hotplug callback if any
		bool hasHotplug = true;
		if (MWUSBRegisterHotPlug(CaptureApp::usbHotplugCallback, this) != MW_SUCCEEDED) {
			_ERROR("Failed register USB device hot plug callback");
			hasHotplug = false;
		}

		_NOTIFY_REPROMON(REPROMON_INFO, appName + " started, v" + CAPTURE_VERSION_STRING);

		do {
			SLEEP_SEC(1);

			if( !targetMwDevPath.empty() && disconnDevContains(targetMwDevPath) ) {
				onCaptureStop("Target USB device instance " + targetMwDevPath + " disconnected");
				targetMwDevPath = "";
				continue;
			}

			HCHANNEL hChannel = NULL;
			if( !findTargetVideoDevice(cfg.has_device_serial_number?cfg.device_serial_number:"",
									   targetVideoDev) ) {
				onCaptureStop(":\tStopped recording. No channels!");
				_VERBOSE("Wait, no channels found");
				continue;
			}

			if(targetVideoDev.channelIndex < 0 ) {
				_VERBOSE("Wait, no valid USB devices found");
				continue;
			}

			_VERBOSE("Found target device: " << targetVideoDev);

			char wPath[256] = {0};
			if(MWGetDevicePath(targetVideoDev.channelIndex, wPath) == MW_SUCCEEDED ) {
				targetMwDevPath = wPath;
				_VERBOSE("Magewell device instance path: " << wPath);
			} else {
				_ERROR("ERROR[006]: Failed MWGetDevicePath");
				targetMwDevPath = "";
			}

			// TODO: check res
			hChannel = MWOpenChannelByPath(wPath);

			// TODO: check res
			MWGetVideoSignalStatus(hChannel, &vssCur);

			frameRate = vssFrameRate(vssCur);

			// just dump current video signal status
			_VERBOSE(vssCur << ". frameRate=" << frameRate);

			if (  ( vssCur.cx > 0 ) && ( vssCur.cx  < 9999 ) && (vssCur.cy > 0) && (vssCur.cy < 9999)) {
				if (recording == 0) {
					// find target video device name/path when not specified explicitly
					if( cfg.ffm_opts.has_v_dev ) {
						targetVideoDevPath = cfg.ffm_opts.v_dev;
						targetBusInfo = "N/A";
					} else {
						VDevPath vdp = getVideoDevicePathBySerial(cfg.video_device_path_pattern,
																  targetVideoDev.serial);
						targetVideoDevPath = vdp.path;
						targetBusInfo = vdp.busInfo;
						if( targetVideoDevPath.empty() ) {
							targetVideoDevPath = "/dev/video_not_found_911";
							_ERROR("ERROR[007]: video device path not found by S/N: " << targetVideoDev.serial
																					  << ", use fallback one: " << targetVideoDevPath);
						}
					}

					if( !cfg.ffm_opts.has_v_dev || !cfg.has_device_serial_number ) {
						_INFO("    <> Found Video Device          ===> "
									  << targetVideoDevPath << ", S/N: " << targetVideoDev.serial
									  << ", " << targetVideoDev.name);
						_INFO("    <>                                  "
									  << "USB bus info         : " << targetBusInfo);
						_INFO("    <>                                  "
									  << "Instance device path : " << targetMwDevPath);
					}

					if( audioEnabled ) {
						if (cfg.ffm_opts.has_a_dev) {
							targetAudioInDevPath = cfg.ffm_opts.a_dev;
						} else {
							std::string alsaDev = "";
							if( cfg.ffm_opts.has_a_alsa_dev ) {
								alsaDev = cfg.ffm_opts.a_alsa_dev;
							}
							targetAudioInDev = getAudioInDevice(targetBusInfo, alsaDev);
							targetAudioInDevPath = targetAudioInDev.alsaDeviceName;
							_INFO("    <> Found Audio-In Device       ===> " << targetAudioInDevPath);
							// set audio card volume
							if( cfg.ffm_opts.a_vol.size()>0 && !targetAudioInDev.alsaCardName.empty() ) {
								for(const auto& entry: cfg.ffm_opts.a_vol) {
									_INFO("    <>                                  Sub-device "
										<< '\"' << entry.first
										<< "/" << getAudioInNameByAlias(entry.first) << '\"'
										<< " volume : "
										<< entry.second.label
									);
								}

								setAudioInVolumeByCard(targetAudioInDev.alsaCardName, cfg.ffm_opts.a_vol);
							}
						}
						_VERBOSE("Target ALSA audio device path: " << targetAudioInDevPath);
					}

					onCaptureStart();
				}
				else {
					if( !vssEquals(vssCur, vssPrev) ) {
						onCaptureStop(":\tStopped recording because something changed.");
					} else
						onCaptureIdle(); // hook to check capture cycle
				}
			}
			else {
				_VERBOSE("No valid video signal detected from target device");

				std::ostringstream message;
				message << ":\tWhack resolution: " << vssCur.cx << "x" << vssCur.cy;
				message << ". Stopped recording";
				onCaptureStop(message.str());
			}

			vssPrev = vssCur;
			safeMWCloseChannel(hChannel);

			// check config changed
			std::string configHash2 = getFileChangeHash(opts.configPath);
			if( configHash!=configHash2 ) {
				_INFO("Config file was modified (" << configHash << " -> " << configHash2 << ") : " << opts.configPath);
				_INFO("Reloading config and restarting capture ...");
				fConfigChanged = true;
				fRun = false;
			}
		} while (fRun && !isSysBreakExec());

		onCaptureStop("Program terminated");

		_NOTIFY_REPROMON(REPROMON_INFO, appName + " terminated");


		if( hasHotplug ) {
			MWUSBUnRegisterHotPlug();
			hasHotplug = false;
		}

		if( fInit )
			MWCaptureExitInstance();

		if( isSysBreakExec() )
			return EX_SYS_BREAK_EXEC;

		if( fConfigChanged )
			return EX_CONFIG_RELOAD;

		return EX_OK;
	}

	void CaptureApp::usbHotplugCallback(MWUSBHOT_PLUG_EVETN event, const char *pszDevicePath, void* pParam) {
		if( pParam==NULL ) return;
		CaptureApp* pApp = reinterpret_cast<CaptureApp*>(pParam);
		switch(event) {
			case USBHOT_PLUG_EVENT_DEVICE_ARRIVED:
				pApp->onUsbDevArrived(pszDevicePath);
				break;
			case USBHOT_PLUG_EVENT_DEVICE_LEFT:
				pApp->onUsbDevLeft(pszDevicePath);
				break;
			default:
				_VERBOSE("Unknown USB hotplug event: " << event << ", " << pszDevicePath);
		}
	}
}
