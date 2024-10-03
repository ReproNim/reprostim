
#include <iostream>
#include <filesystem>

// make log level to be upper case, can be also placed under include/spdlog/tweakme.h
#define SPDLOG_LEVEL_NAMES  { "TRACE", "DEBUG", "INFO",  "WARN", "ERROR", "CRITICAL", "OFF" };

#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>
#include "reprostim/CaptureLib.h"

namespace fs = std::filesystem;

namespace reprostim {

	volatile LogPattern g_logPattern = LogPattern::SIMPLE; // set default log pattern
	volatile int g_verbose = 0;
	thread_local SessionLogger_ptr tl_pSessionLogger = nullptr;
	std::shared_ptr<spdlog::logger> g_pGlobalLogger = nullptr;

	std::string buildLogPrefix(LogPattern pattern, LogLevel level) {
		if( pattern != LogPattern::FULL ) {
			return "";
		}

		std::stringstream ss;
		const Timestamp &ts = CURRENT_TIMESTAMP();

		ss << getTimeFormatStr(ts, "%Y-%m-%d %H:%M:%S");

		// put also ms precision
		auto nowMs = std::chrono::duration_cast<std::chrono::milliseconds>(ts.time_since_epoch()) % 1000;
		ss << '.' << std::setw(3) << std::setfill('0') << nowMs.count();

		// add log level
		switch( level ) {
			case LogLevel::DEBUG:
				ss << " [DEBUG]";
				break;
			case LogLevel::INFO:
				ss << " [INFO]";
				break;
			case LogLevel::WARN:
				ss << " [WARN]";
				break;
			case LogLevel::ERROR:
				ss << " [ERROR]";
				break;
			default:
				ss << " [UNKNOWN]";
				break;
		}

		// add thread id
		//std::thread::id thread_id = std::this_thread::get_id();
		ss << " [" << spdlog::details::os::thread_id() << "]";

		ss << " ";
		return ss.str();
	}

	LogLevel parseLogLevel(const std::string &level) {
		if( level == "DEBUG" ) {
			return LogLevel::DEBUG;
		} else if( level == "INFO" ) {
			return LogLevel::INFO;
		} else if( level == "WARN" ) {
			return LogLevel::WARN;
		} else if( level == "ERROR" ) {
			return LogLevel::ERROR;
		} else if( level == "OFF" ) {
			return LogLevel::OFF;
		} else {
			try {
				int n = std::stoi(level);
				if( n>=LogLevel::OFF && n<=LogLevel::ERROR ) {
					return static_cast<LogLevel>(n);
				}
			} catch( std::exception &e ) {
				_ERROR("Failed to parse log level: " << level << ", " << e.what());
			}
			return LogLevel::OFF;
		}
	}

	void registerFileLogger(const std::string &name, const std::string &filePath, int level)
	{
		// Create a logger with two sinks: stdout and file
		auto console_sink = std::make_shared<spdlog::sinks::ansicolor_stdout_sink_mt>();
		auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(filePath, false);

		// Create a logger with the two sinks
		auto logger = std::make_shared<spdlog::logger>(name,
													   spdlog::sinks_init_list{console_sink, file_sink});

		// Set the logging level
		switch( level ) {
			case LogLevel::DEBUG:
				logger->set_level(spdlog::level::debug);
				break;
			case LogLevel::INFO:
				logger->set_level(spdlog::level::info);
				break;
			case LogLevel::WARN:
				logger->set_level(spdlog::level::warn);
				break;
			case LogLevel::ERROR:
				logger->set_level(spdlog::level::err);
				break;
			default:
				logger->set_level(spdlog::level::off);
				break;
		}

		// Register the logger globally
		spdlog::register_logger(logger);

		// Redirect stdout to the file
		freopen(filePath.c_str(), "a", stdout);
		freopen(filePath.c_str(), "a", stderr);
		//logger->sinks().push_back(console_sink);
		g_pGlobalLogger = logger;
	}

	void unregisterFileLogger(const std::string &name)
	{
		spdlog::drop(name);
		g_pGlobalLogger = nullptr;
	}

	///////////////////////////////////////////////////////////////////////////////
	// FileLogger implementation

	// FileLogger::Impl private implementation
	class FileLogger::Impl {
	private:
		std::shared_ptr<spdlog::logger> m_pLogger;
		std::string                     m_sName;
	public:

		void close() {
			if( m_pLogger ) {
				// Flush all logs
				m_pLogger->flush();
				m_pLogger.reset();
				if( !m_sName.empty() ) {
					// Force logger to be dropped
					spdlog::drop(m_sName);
					m_sName = "";
				}
			}
		}

		inline std::shared_ptr<spdlog::logger>& getLogger() {
			return m_pLogger;
		}

		inline bool isOpen() const {
			return m_pLogger!=nullptr;
		}

		void log(int level, const std::string &msg) {
			if( m_pLogger ) {
				switch( level ) {
					case LogLevel::DEBUG:
						m_pLogger->debug(msg);
						break;
					case LogLevel::INFO:
						m_pLogger->info(msg);
						break;
					case LogLevel::WARN:
						m_pLogger->warn(msg);
						break;
					case LogLevel::ERROR:
						m_pLogger->error(msg);
						break;
				}
			}
		}

		void open(const std::string &name,
				  const std::string &filePath,
				  const std::string &pattern) {
			if( isOpen() ) {
				close();
			}
			m_sName = name;
			m_pLogger = spdlog::basic_logger_mt(name, filePath);
			m_pLogger->set_level(spdlog::level::trace);
			if( !pattern.empty() ) {
				m_pLogger->set_pattern(pattern);
			}
			// NOTE: in future we can add more options here
			// for realtime logging
			//
			//m_pLogger->flush_on(spdlog::level::trace);
			// available only in newer version in future
			// m_pLogger->set_flush_interval(std::chrono::milliseconds(1000));
		}
	};

	// FileLogger implementation
	FileLogger::FileLogger(): m_pImpl(new Impl()) {
		m_nLevel = LogLevel::OFF;
	}

	FileLogger::~FileLogger() {
		close();
	}

	void FileLogger::log(int level, const std::string &msg) {
		if( level>=m_nLevel ) {
			m_pImpl->log(level, msg);
		}
	}

	std::string FileLogger::move(const std::string& newFilePath) {
		if( m_pImpl->isOpen() ) {
			_ERROR("Can't rename log file while logger is open:  " << m_sName << ", " << m_sFilePath);
		}
		if( std::filesystem::exists(m_sFilePath) ) {
			rename(m_sFilePath.c_str(), newFilePath.c_str());
			return newFilePath;
		}
		return m_sFilePath;
	}

	void FileLogger::open(const std::string &name,
						  const std::string &filePath, int level,
						  const std::string &pattern) {
		m_sName = name;
		m_sFilePath = filePath;
		m_nLevel = level;
		m_pImpl->open(name, filePath, pattern);
	}

	void FileLogger::close() {
		m_pImpl->close();
	}

}