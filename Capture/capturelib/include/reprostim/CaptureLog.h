#ifndef CAPTURE_CAPTURELOG_H
#define CAPTURE_CAPTURELOG_H

////////////////////////////////////////////////////////////////////////////////
// Macros

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
#define _VERBOSE(expr) if( isVerbose() ) { std::cout << expr << std::endl; _SESSION_LOG_DEBUG(expr); }
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
	if( p ) { p->info("Session logging end: "+p->getName()); p->close(); p->move(newFilePath); } \
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

#ifndef _METADATA_MAGIC_BEGIN
#define _METADATA_MAGIC_BEGIN "REPROSTIM-METADATA-JSON: "
#endif

#ifndef _METADATA_MAGIC_END
#define _METADATA_MAGIC_END " :REPROSTIM-METADATA-JSON"
#endif

#ifndef _METADATA_LOG
#define _METADATA_LOG(data) _INFO(_METADATA_MAGIC_BEGIN << data << _METADATA_MAGIC_END);
#endif

#ifndef _FILE_LOGGER_NAME
#define _FILE_LOGGER_NAME "logger"
#endif

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

	////////////////////////////////////////////////////////////////////////////////
	// Functions

	LogLevel parseLogLevel(const std::string &level);
	void     registerFileLogger(const std::string &name, const std::string &filePath, int level = LogLevel::DEBUG);
	void     unregisterFileLogger(const std::string &name);

	////////////////////////////////////////////////////////////////////////////////
	// Classes

	class FileLogger {
	private:
		class Impl; // private logger implementation
		std::unique_ptr<Impl>           m_pImpl;
		std::string                     m_sFilePath;
		volatile int                    m_nLevel;
		std::string                     m_sName;

		void log(int level, const std::string &msg);
	public:
		FileLogger();
		~FileLogger();

		void close();
		void debug_(const std::string &msg);
		void error(const std::string &msg);
		const std::string& getFilePath() const;
		const std::string& getName() const;
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

	inline const std::string& FileLogger::getName() const {
		return m_sName;
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

	// Session logger pointer type
	using SessionLogger_ptr = std::shared_ptr<FileLogger>;

	//////////////////////////////////////////////////////////////////////////
	// Global variables

	extern volatile int g_verbose;

	// global TLS variable to hold local session logger
	extern thread_local SessionLogger_ptr tl_pSessionLogger;

	//////////////////////////////////////////////////////////////////////////
	// Inline functions

	inline bool isVerbose() {
		return g_verbose>0;
	}

	inline void setVerbose(bool verbose) {
		g_verbose = verbose ? 1 : 0;
	}

}
#endif //CAPTURE_CAPTURELOG_H
