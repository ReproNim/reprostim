#ifndef CAPTURE_CAPTUREAPP_H
#define CAPTURE_CAPTUREAPP_H

namespace reprostim {

	struct FfmpegOpts {
		std::string a_fmt;
		std::string a_nchan;
		std::string a_dev;
		bool        has_a_dev = false;
		std::string a_opt;
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
		std::string device_serial_number;
		bool        has_device_serial_number = false;
		std::string video_device_path_pattern;
		FfmpegOpts  ffm_opts;
	};

	// App command-line options and args
	struct AppOpts {
		std::string configPath;
		std::string homePath;
		std::string outPath;
		bool        verbose = false;
	};


	class CaptureApp {
	protected:
		// setup data
		std::string appName;

		// config data
		AppOpts   opts;
		AppConfig cfg;
		bool      verbose;

		// session runtime data
		std::string               configHash;
		std::string               frameRate;
		std::string               init_ts;
		int                       recording;
		std::string               start_ts;
		MWCAP_VIDEO_SIGNAL_STATUS vssCur; // current video signal status
		MWCAP_VIDEO_SIGNAL_STATUS vssPrev; // previous video signal status
		VideoDevice               targetDev;
		std::string               targetBusInfo;
		std::string               targetVideoDevPath;
		std::string               targetAudioDevPath;



	public:
		virtual bool loadConfig(AppConfig& cfg, const std::string& pathConfig);
		virtual void onCaptureStart();
		virtual void onCaptureStop(const std::string& message);
		virtual int  parseOpts(AppOpts& opts, int argc, char* argv[]);
		int  run(int argc, char* argv[]);
	};

}
#endif //CAPTURE_CAPTUREAPP_H
