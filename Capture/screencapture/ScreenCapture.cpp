#include <iostream>
#include <unistd.h>
#include <filesystem>
#include <atomic>
#include <thread>
#include <sysexits.h>
#include "ScreenCapture.h"


using namespace reprostim;

static std::atomic<int> g_activeSessionId(0);

inline void rtSafeDelete(RecordingThread* &prt) {
	if( prt ) {
		if( prt->isRunning() ) {
			prt->stop();
		}
		if( !prt->isRunning() ) {
			delete prt;
		}
		// NOTE: memory-leaks are possible in rare conditions
		prt = nullptr;
	}
}

////////////////////////////////////////////////////////////////////////////
// ScreenCaptureApp class

ScreenCaptureApp::ScreenCaptureApp() {
	appName = "ScreenCapture";
	audioEnabled = false;
	m_prtCur = nullptr;
	m_prtPrev = nullptr;
}

ScreenCaptureApp::~ScreenCaptureApp() {
	rtSafeDelete(m_prtCur);
	rtSafeDelete(m_prtPrev);
}

void ScreenCaptureApp::onCaptureStart() {
	g_activeSessionId.fetch_add(1);
	int sessionId = g_activeSessionId;
	_INFO("Start recording snapshots, sessionId=" << sessionId);
	SLEEP_MS(200);
	recording = 1;

	rtSafeDelete(m_prtPrev);
	m_prtPrev = m_prtCur;
	rtSafeDelete(m_prtPrev);

	m_prtCur = new RecordingThread(RecordingParams{
			opts.verbose,
			sessionId,
			vssCur.cx, vssCur.cy,
			m_scOpts.threshold,
			opts.outPath,
			targetVideoDevPath,
			m_scOpts.dump_raw
	});

	m_prtCur->start();
}

void ScreenCaptureApp::onCaptureStop(const std::string& message) {
	if( recording>0 ) {
		int sessionId = g_activeSessionId.fetch_add(1);
		_INFO("Stop recording snapshots. " << sessionId);
		rtSafeDelete(m_prtPrev);
		m_prtPrev = m_prtCur;
		rtSafeDelete(m_prtPrev);
		m_prtCur = nullptr;
		recording = 0;
		SLEEP_SEC(1);
	}
}

bool ScreenCaptureApp::onLoadConfig(AppConfig &cfg, const std::string &pathConfig, YAML::Node doc) {
	if( doc["sc_opts"] ) {
		YAML::Node node = doc["sc_opts"];
		m_scOpts.dump_raw = node["dump_raw"].as<bool>();
		m_scOpts.threshold = node["threshold"].as<int>();
	} else {
		m_scOpts.threshold = 0;
		m_scOpts.dump_raw = false;
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
								 "\t-v       \tVerbose, provides detailed information to stdout\n"
								 "\t-h       \tPrint this help string\n";

	int c = 0;
	if (argc == 1) {
		_ERROR("ERROR[006]: Please provide valid options");
		_INFO(HELP_STR);
		return EX_USAGE;
	}

	while( ( c = getopt (argc, argv, "d:o:c:hv") ) != -1 ) {
		switch(c) {
			case 'o':
				if(optarg) opts.outPath = optarg;
				break;
			case 'c':
				if(optarg) opts.configPath = optarg;
				break;
			case 'd':
				if(optarg) opts.homePath = optarg;
				break;
			case 'h':
				_INFO(HELP_STR);
				return 1;
			case 'v':
				opts.verbose = true;
				break;
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


