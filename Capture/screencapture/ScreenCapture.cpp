#include <iostream>
#include <unistd.h>
#include <atomic>
#include <thread>
#include <sysexits.h>
#include <getopt.h>
#include "ScreenCapture.h"


using namespace reprostim;

static std::atomic<int> g_activeSessionId(0);

////////////////////////////////////////////////////////////////////////////
// ScreenCaptureApp class

ScreenCaptureApp::ScreenCaptureApp() {
	appName = "reprostim-screencapture";
	audioEnabled = false;
}

ScreenCaptureApp::~ScreenCaptureApp() {
	m_recExec.shutdown();
}

void ScreenCaptureApp::onCaptureStart() {
	start_ts = getTimeStr();
	g_activeSessionId.fetch_add(1);
	int sessionId = g_activeSessionId;
	SessionLogger_ptr pLogger = createSessionLogger("session_" + std::to_string(sessionId),
													opts.outPath + "/" + start_ts + "_.log");
	_SESSION_LOG_BEGIN(pLogger);
	_INFO("Start recording snapshots in session " << sessionId);
	SLEEP_MS(200);
	recording = 1;

	RecordingThread* pt = RecordingThread::newInstance(RecordingParams{
			opts.verbose,
			sessionId,
			vssCur.cx, vssCur.cy,
			m_scOpts.threshold,
			opts.outPath,
			targetVideoDevPath,
			m_scOpts.dump_raw,
			m_scOpts.interval_ms,
			start_ts,
			pLogger
	});

	m_recExec.schedule(pt);
}

void ScreenCaptureApp::onCaptureStop(const std::string& message) {
	if( recording>0 ) {
		_INFO("Stop recording snapshots for session " << g_activeSessionId << ". " << message);
		_SESSION_LOG_END();
		m_recExec.schedule(nullptr);
		recording = 0;
		SLEEP_SEC(1);
	}
}

bool ScreenCaptureApp::onLoadConfig(AppConfig &cfg, const std::string &pathConfig, YAML::Node doc) {
	if( doc["sc_opts"] ) {
		YAML::Node node = doc["sc_opts"];
		m_scOpts.dump_raw = node["dump_raw"].as<bool>();
		m_scOpts.interval_ms = node["interval_ms"].as<int>();
		m_scOpts.threshold = node["threshold"].as<int>();
	} else {
		m_scOpts.dump_raw = false;
		m_scOpts.interval_ms = 0;
		m_scOpts.threshold = 0;
	}
	return true;
}

int ScreenCaptureApp::parseOpts(AppOpts& opts, int argc, char* argv[]) {
	const std::string HELP_STR = "Usage: reprostim-screencapture -d <path> [-o <path> | -h | -v ]\n\n"
								 "\t-d <path>\t$REPROSTIM_HOME directory (not optional)\n"
								 "\t-o <path>\tOutput directory where to save recordings (optional)\n"
								 "\t         \tDefaults to $REPROSTIM_HOME/Screens\n"
								 "\t-c <path>\tPath to configuration config.yaml file (optional)\n"
								 "\t         \tDefaults to $REPROSTIM_HOME/config.yaml\n"
								 "\t-v, --verbose\n"
								 "\t         \tVerbose, provides detailed information to stdout\n"
								 "\t-l, --list-devices\n"
								 "\t         \tList devices, only audio is supported\n"
								 "\t-V, --version\n"
								 "\t         \tPrint version information\n"
								 "\t-h, --help\n"
								 "\t         \tPrint this help string\n";

	int c = 0;
	if (argc == 1) {
		_ERROR("ERROR[006]: Please provide valid options");
		_INFO(HELP_STR);
		return EX_USAGE;
	}

	struct option longOpts[] = {
			{"help", no_argument, nullptr, 'h'},
			{"verbose", no_argument, nullptr, 'v'},
			{"version", no_argument, nullptr, 'V'},
			{"list-devices", no_argument, nullptr, 'l'},
			{nullptr, 0, nullptr, 0}
	};

	while ((c = getopt_long(argc, argv, "o:c:d:hvVl", longOpts, nullptr)) != -1) {
		switch (c) {
			case 'o':
				if (optarg) opts.outPath = optarg;
				break;
			case 'c':
				if (optarg) opts.configPath = optarg;
				break;
			case 'd':
				if (optarg) opts.homePath = optarg;
				break;
			case 'h':
				_INFO(HELP_STR);
				return 1;
			case 'l':
				listDevices();
				return 1;
			case 'v':
				opts.verbose = true;
				break;
			case 'V':
				printVersion();
				return 1;
		}
	}


	// Terminate when REPROSTIM_HOME not specified
	if ( opts.homePath.empty() ){
		_ERROR("ERROR[007]: REPROSTIM_HOME not specified, see -d");
		_INFO(HELP_STR);
		return EX_USAGE;
	}

	// Set config filename if not specified on input
	if ( opts.configPath.empty() ) {
		opts.configPath = opts.homePath + "/config.yaml";
	}

	// Set output directory if not specified on input
	if( opts.outPath.empty() ) {
		opts.outPath = opts.homePath + "/Screens";
	}
	return EX_OK;
}


