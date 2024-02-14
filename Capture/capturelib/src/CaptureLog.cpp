
#include <iostream>
#include <filesystem>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>
#include "CaptureLib.h"

namespace fs = std::filesystem;

namespace reprostim {

	thread_local SessionLogger_ptr tl_pSessionLogger = nullptr;

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