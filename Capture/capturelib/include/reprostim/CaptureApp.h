#ifndef CAPTURE_CAPTUREAPP_H
#define CAPTURE_CAPTUREAPP_H

#include <unistd.h>
#include <optional>
#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureThreading.h"
#include "reprostim/CaptureRepromon.h"
#include "yaml-cpp/yaml.h"

namespace reprostim {

	// Macros to define message to be sent to repromon system
	#ifndef _NOTIFY_REPROMON
	#define _NOTIFY_REPROMON(...) if (fRepromonEnabled) { \
    	RepromonMessage msg = { __VA_ARGS__ };            \
        if( msg.event_on.empty() ) { msg.event_on = getTimeIsoStr(); } \
        if( msg.registered_on.empty() ) { msg.registered_on = getTimeIsoStr(); } \
		pRepromonQueue->push(msg);                        \
	}
	#endif // _NOTIFY_REPROMON

	// optional con/duct options
	struct ConductOpts {
		bool         enabled = false;
		std::string  cmd;
		std::string  duct_bin;
	};

	struct FfmpegOpts {
		std::string a_fmt;
		std::string a_nchan;
		std::string a_dev;
		bool        has_a_dev = false;
		std::string a_alsa_dev; // calculated option
		bool        has_a_alsa_dev = false;
		std::string a_opt;
		std::unordered_map<std::string, AudioVolume> a_vol;
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
		std::string  device_serial_number;
		bool         has_device_serial_number = false;
		bool         session_logger_enabled = false;
		LogLevel     session_logger_level = LogLevel::OFF;
		std::string  session_logger_pattern;
		std::string  video_device_path_pattern;
		ConductOpts  conduct_opts;
		RepromonOpts repromon_opts;
		FfmpegOpts   ffm_opts;
	};

	// App command-line options and args
	struct AppOpts {
		std::string configPath;
		std::string homePath;
		std::string outPathTempl;
		bool        verbose = false;
	};

	class CaptureApp {
	private:
		_DECLARE_CLASS_WITH_SYNC();

		std::set<std::string> m_disconnDevs;

		inline void disconnDevAdd(const std::string& devPath);
		inline bool disconnDevContains(const std::string& devPath) const;
		inline void disconnDevRemove(const std::string& devPath);

	protected:

		// setup data
		std::string appName;
		bool        audioEnabled;

		// config data
		AppOpts   opts;
		AppConfig cfg;

		// repromon message queue
		std::unique_ptr<RepromonQueue>  pRepromonQueue;
		bool                            fRepromonEnabled;

		// session runtime data
		std::string               configHash;
		std::string               frameRate;
		std::string               outPath;
		int                       recording;
		Timestamp                 tsInit;
		std::string               init_ts;
		Timestamp                 tsStart;
		std::string               start_ts;
		MWCAP_VIDEO_SIGNAL_STATUS vssCur; // current video signal status
		MWCAP_VIDEO_SIGNAL_STATUS vssPrev; // previous video signal status
		AudioInDevice             targetAudioInDev;
		VideoDevice               targetVideoDev;
		std::string               targetBusInfo;
		std::string               targetMwDevPath;
		std::string               targetVideoDevPath;
		std::string               targetAudioInDevPath;

		static void usbHotplugCallback(MWUSBHOT_PLUG_EVETN event, const char *pszDevicePath, void* pParam);

	public:
		CaptureApp();
		~CaptureApp();

		std::string createOutPath(const std::optional<Timestamp> &ts = std::nullopt, bool fCreateDir = true);
		SessionLogger_ptr createSessionLogger(const std::string& name, const std::string& filePath);
		void listDevices(const std::string& devices);
		virtual bool loadConfig(AppConfig& cfg, const std::string& pathConfig);
		virtual void onCaptureIdle();
		virtual void onCaptureStart();
		virtual void onCaptureStop(const std::string& message);
		virtual bool onLoadConfig(AppConfig& cfg, const std::string& pathConfig, YAML::Node doc);
		virtual void onUsbDevArrived(const std::string& devPath);
		virtual void onUsbDevLeft(const std::string& devPath);
		virtual int  parseOpts(AppOpts& opts, int argc, char* argv[]);
		void printVersion(bool fExpanded = false);
		int  run(int argc, char* argv[]);
	};

	// methods
	int checkConduct(const ConductOpts& opts);

	// inline methods

	inline void CaptureApp::disconnDevAdd(const std::string& devPath) {
		_SYNC();
		m_disconnDevs.insert(devPath);
	}

	inline bool CaptureApp::disconnDevContains(const std::string& devPath) const {
		_SYNC();
		return m_disconnDevs.find(devPath)!=m_disconnDevs.end();
	}

	inline void CaptureApp::disconnDevRemove(const std::string& devPath) {
		_SYNC();
		m_disconnDevs.erase(devPath);
	}

	// Default main entry point implementation
	// for use in main.cpp in application based
	// on CaptureApp
	template<typename T>
	int mainImpl(int argc, char* argv[]) {
		int res = EXIT_SUCCESS;
		do {
			T app;
			res = app.run(argc, argv);
			optind = 0; // force restart argument scanning for getopt
		} while(res == EX_CONFIG_RELOAD);
		return res;
	}

}
#endif //CAPTURE_CAPTUREAPP_H
