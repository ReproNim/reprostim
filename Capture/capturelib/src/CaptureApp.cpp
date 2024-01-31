#include <iostream>
#include <sstream>
#include <chrono>
#include <csignal>
#include <thread>
#include <sysexits.h>
#include "CaptureApp.h"

namespace reprostim {

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
		return this->onLoadConfig(cfg, pathConfig, doc);
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

	int CaptureApp::parseOpts(AppOpts& opts, int argc, char* argv[]) {
		_INFO("TODO: parseOpts");
		return EX_OK;
	}

	void CaptureApp::printVersion() {
		_INFO(appName << " " << CAPTURE_VERSION_STRING);
		_INFO(" Build date " << CAPTURE_VERSION_DATE);
	}

	int CaptureApp::run(int argc, char* argv[]) {

		std::signal(SIGINT,  signalHandler);
		std::signal(SIGTERM, signalHandler);
		std::signal(SIGKILL, signalHandler);

		const int res1 = parseOpts(opts, argc, argv);
		verbose = opts.verbose;

		if( res1==1 ) return EX_OK; // help message
		if( res1!=EX_OK ) return res1;

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

		const int res2 = checkSystem(verbose);
		if( res2!=EX_OK ) {
			// problem with system configuration and installed packages
			return res2;
		}

		// calculated options
		configHash = getFileChangeHash(opts.configPath);

		// current video signal status
		vssCur = {};

		// previous video signal status
		vssPrev = {};

		bool fRun = true;
		bool fConfigChanged = false;
		recording = 0;

		MW_RESULT mr = MW_SUCCEEDED;

		init_ts = getTimeStr();
		_INFO(init_ts << ": <><><> Starting " << appName << " <><><>");
		_INFO("    <> Saving output to            ===> " << opts.outPath);
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

		BOOL fInit = MWCaptureInitInstance();
		if( !fInit )
			_ERROR("ERROR[005]: Failed MWCaptureInitInstance");

		_VERBOSE("MWCapture SDK version: " << mwcSdkVersion());

		do {
			SLEEP_SEC(1);
			HCHANNEL hChannel = NULL;
			if( !findTargetVideoDevice(opts.verbose,
									   cfg.has_device_serial_number?cfg.device_serial_number:"",
									   targetDev) ) {
				onCaptureStop(":\tStopped recording. No channels!");
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

					if( audioEnabled ) {
						if (cfg.ffm_opts.has_a_dev) {
							targetAudioDevPath = cfg.ffm_opts.a_dev;
						} else {
							targetAudioDevPath = getAudioDevicePath(opts.verbose, targetBusInfo);
							_INFO("    <> Found Audio Device          ===> " << targetAudioDevPath);
						}
						_VERBOSE("Target ALSA audio device path: " << targetAudioDevPath);
					}

					onCaptureStart();
				}
				else {
					if( !vssEquals(vssCur, vssPrev) ) {
						onCaptureStop(":\tStopped recording because something changed.");
					}
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

		if( fInit )
			MWCaptureExitInstance();

		if( isSysBreakExec() )
			return EX_SYS_BREAK_EXEC;

		if( fConfigChanged )
			return EX_CONFIG_RELOAD;

		return EX_OK;
	}

}
