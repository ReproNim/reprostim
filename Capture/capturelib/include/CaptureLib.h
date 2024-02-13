#ifndef REPROSTIM_CAPTURELIB_H
#define REPROSTIM_CAPTURELIB_H

#include <string>
#include <functional>
#include <iostream>
#include <sstream>
#include <vector>
#include <chrono>
#include <thread>
#include <spdlog/spdlog.h>
#include "LibMWCapture/MWCapture.h"

#include "CaptureVer.h"

/*########################### Common macros ############################*/

#ifndef _ERROR
#define _ERROR(expr) std::cerr << expr << std::endl; _SESSION_LOG_ERROR(expr)
#endif

#ifndef _INFO
#define _INFO(expr) std::cout << expr << std::endl; _SESSION_LOG_INFO(expr)
#endif

#ifndef _INFO_RAW
#define _INFO_RAW(expr) std::cout << expr; _SESSION_LOG_INFO(expr)
#endif

#ifndef _VERBOSE
#define _VERBOSE(expr) if( verbose ) { std::cout << expr << std::endl; _SESSION_LOG_DEBUG(expr); }
#endif

// Session logger related macros

#ifndef _SESSION_LOG_BEGIN
#define _SESSION_LOG_BEGIN(logger) tl_pSessionLogger = logger
#endif

#ifndef _SESSION_LOG_END
#define _SESSION_LOG_END() tl_pSessionLogger = nullptr
#endif

#ifndef _SESSION_LOG_END_CLOSE_RENAME
#define _SESSION_LOG_END_CLOSE_RENAME(newFilePath) { \
	SessionLogger_ptr p = tl_pSessionLogger; \
	_SESSION_LOG_END(); \
	if( p ) { p->close(); p->move(newFilePath); } \
}
#endif

#ifndef _SESSION_LOG_DEBUG
#define _SESSION_LOG_DEBUG(expr) if( tl_pSessionLogger && tl_pSessionLogger->isDebugEnabled() ) { std::ostringstream _stm_expr; _stm_expr << expr; tl_pSessionLogger->debug_(_stm_expr.str()); }
#endif

#ifndef _SESSION_LOG_ERROR
#define _SESSION_LOG_ERROR(expr) if( tl_pSessionLogger && tl_pSessionLogger->isErrorEnabled() ) { std::ostringstream _stm_expr; _stm_expr << expr;  tl_pSessionLogger->error(_stm_expr.str()); }
#endif

#ifndef _SESSION_LOG_INFO
#define _SESSION_LOG_INFO(expr) if( tl_pSessionLogger && tl_pSessionLogger->isInfoEnabled() ) { std::ostringstream _stm_expr; _stm_expr << expr;  tl_pSessionLogger->info(_stm_expr.str()); }
#endif

#ifndef _SESSION_LOG_WARN
#define _SESSION_LOG_WARN(expr) if( tl_pSessionLogger && tl_pSessionLogger->isWarnEnabled() ) { std::ostringstream _stm_expr; _stm_expr << expr;  tl_pSessionLogger->warn(_stm_expr.str()); }
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

	/////////////////////////////////////////////////////////////////////
	// Enums

	enum LogLevel:int {
		OFF   = 0,
		DEBUG = 1,
		INFO  = 2,
		WARN  = 3,
		ERROR = 4
	};

	//////////////////////////////////////////////////////////////////////////
	// Structs
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

	bool checkOutDir(bool verbose, const std::string &outDir);

	int checkSystem(bool verbose);

	std::string chiToString(MWCAP_CHANNEL_INFO &info);

	std::string exec(bool verbose, const std::string &cmd, bool showStdout = false,
					 int maxResLen = -1,
					 std::function<bool()> isTerminated = [](){ return false; });

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

	LogLevel parseLogLevel(const std::string &level);

	void safeMWCloseChannel(HCHANNEL&hChannel);

	void setSysBreakExec(bool fBreak);

	std::string vdToString(VideoDevice &vd);

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

	//////////////////////////////////////////////////////////////////////////
	// Classes

	class FileLogger {
	private:
		std::string                     m_sFilePath;
		volatile int                    m_nLevel;
		std::shared_ptr<spdlog::logger> m_pLogger;
		std::string                     m_sName;
		void log(int level, const std::string &msg);
	public:
		FileLogger();
		~FileLogger();

		void close();
		void debug_(const std::string &msg);
		void error(const std::string &msg);
		const std::string& getFilePath() const;
		void info(const std::string &msg);
		bool isDebugEnabled() const;
		bool isErrorEnabled() const;
		bool isInfoEnabled() const;
		bool isWarnEnabled() const;
		std::string move(const std::string& newFilePath);
		void open(const std::string& name, const std::string &filePath, int level = LogLevel::INFO,
				  const std::string& pattern = "");
		void setLevel(int level);
		void warn(const std::string &msg);
	};

	inline void FileLogger::debug_(const std::string &msg) {
		log(LogLevel::DEBUG, msg);
	}

	inline void FileLogger::error(const std::string &msg) {
		log(LogLevel::ERROR, msg);
	}

	inline const std::string& FileLogger::getFilePath() const {
		return m_sFilePath;
	}

	inline void FileLogger::info(const std::string &msg) {
		log(LogLevel::INFO, msg);
	}

	inline bool FileLogger::isDebugEnabled() const {
		return m_nLevel <= LogLevel::DEBUG;
	}

	inline bool FileLogger::isErrorEnabled() const {
		return m_nLevel <= LogLevel::ERROR;
	}

	inline bool FileLogger::isInfoEnabled() const {
		return m_nLevel <= LogLevel::INFO;
	}

	inline bool FileLogger::isWarnEnabled() const {
		return m_nLevel <= LogLevel::WARN;
	}

	inline void FileLogger::setLevel(int level) {
		m_nLevel = level;
	}

	inline void FileLogger::warn(const std::string &msg) {
		log(LogLevel::WARN, msg);
	}

	using SessionLogger_ptr = std::shared_ptr<FileLogger>;

	extern thread_local SessionLogger_ptr tl_pSessionLogger;

}
#endif //REPROSTIM_CAPTURELIB_H
