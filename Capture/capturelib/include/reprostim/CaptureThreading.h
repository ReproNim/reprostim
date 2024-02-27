#ifndef CAPTURE_WORKERTHREAD_H
#define CAPTURE_WORKERTHREAD_H

#include <iostream>
#include <atomic>
#include <thread>
#include <mutex>
#include "reprostim/CaptureLib.h"

//////////////////////////////////////////////////////////////////////////
// Macros

#ifndef _SYNC_LOCK
#define _SYNC_LOCK(mutex_) std::lock_guard<std::mutex> _sync_lock(mutex_)
#endif //_SYNC_LOCK

#ifndef _DECLARE_CLASS_WITH_SYNC
#define _DECLARE_CLASS_WITH_SYNC() mutable std::mutex _this_mutex_
#endif //_DECLARE_CLASS_WITH_SYNC

#ifndef _SYNC
#define _SYNC() _SYNC_LOCK(_this_mutex_)
#endif //_SYNC


namespace reprostim {

	//////////////////////////////////////////////////////////////////////////
	// WorkerThread template

	template<typename T>
	class WorkerThread {

	private:
		void runInternal();

	protected:
		const T m_params;
		std::atomic<bool> m_running;
		std::atomic<bool> m_terminated;

	public:
		WorkerThread(const T &params);
		virtual ~WorkerThread();

		const T& getParams() const;
		bool isRunning() const;
		bool isTerminated() const;
		void run();
		void start();
		void stop();

		// static helpers
		static WorkerThread<T>* newInstance(const T &params);
		static void deleteInstance(WorkerThread<T>* p);
	};

	//////////////////////////////////////////////////////////////////////////
	// WorkerThread Implementation

	template<typename T>
	WorkerThread<T>::WorkerThread(const T &params) : m_params(params) {
		m_running = false;
		m_terminated = false;
	}

	template<typename T>
	WorkerThread<T>::~WorkerThread() {
	}

	template<typename T>
	inline const T& WorkerThread<T>::getParams() const {
		return m_params;
	}

	template<typename T>
	inline bool WorkerThread<T>::isRunning() const {
		return m_running;
	}

	template<typename T>
	inline bool WorkerThread<T>::isTerminated() const {
		return m_terminated;
	}

	template<typename T>
	void WorkerThread<T>::run() {
		// provide own template specialization
		_INFO("WorkerThread::run: not implemented");
	}

	template<typename T>
	void WorkerThread<T>::runInternal() {
		m_running = true;
		try {
			run();
		} catch (std::exception &e) {
			_ERROR("WorkerThread::runInternal: " << e.what());
		} catch (...) {
			_ERROR("WorkerThread::runInternal: unknown exception");
		}
		m_running = false;
	}

	template<typename T>
	void WorkerThread<T>::start() {
		m_running = false;
		m_terminated = false;
		std::thread t(&WorkerThread::runInternal, this);
		for (int i = 0; i < 10; i++) {
			SLEEP_MS(100);
			if (m_running) {
				break;
			}
		}
		t.detach();
	}

	template<typename T>
	void WorkerThread<T>::stop() {
		m_terminated = true;
		for (int i = 0; i < 10; i++) {
			SLEEP_MS(100);
			if (!m_running) {
				break;
			}
		}
	}

	template<typename T>
	inline WorkerThread<T>* WorkerThread<T>::newInstance(const T &params) {
		return new WorkerThread<T>(params);
	}

	template<typename T>
	inline void WorkerThread<T>::deleteInstance(WorkerThread<T>* p) {
		if( p!= nullptr ) {
			delete p;
		}
	}


	//////////////////////////////////////////////////////////////////////////
	// SingleThreadExecutor

	template<typename T>
	class SingleThreadExecutor {
	private:
		T*  m_pCur;
		T*  m_pPrev;

		void safeDelete(T* &p);

	public:
		SingleThreadExecutor();
		~SingleThreadExecutor();

		T* getCurrentThread() const;
		void schedule(T* pThread);
		void shutdown();
	};

	template<typename T>
	inline SingleThreadExecutor<T>::SingleThreadExecutor() {
		m_pCur = nullptr;
		m_pPrev = nullptr;
	}

	template<typename T>
	inline SingleThreadExecutor<T>::~SingleThreadExecutor() {
		safeDelete(m_pCur);
		safeDelete(m_pPrev);
	}

	template<typename T>
	T* SingleThreadExecutor<T>::getCurrentThread() const {
		return m_pCur;
	}

	template<typename T>
	inline void SingleThreadExecutor<T>::safeDelete(T* &p) {
		if( p ) {
			if( p->isRunning() ) {
				p->stop();
			}
			if( !p->isRunning() ) {
				T::deleteInstance(p);
			} else {
				// NOTE: memory-leaks are possible in rare conditions
				_INFO("Failed to stop worker thread: " << p);
			}
			p = nullptr;
		}
	}

	template<typename T>
	void SingleThreadExecutor<T>::schedule(T* pThread) {
		safeDelete(m_pPrev);
		m_pPrev = m_pCur;
		safeDelete(m_pPrev);

		m_pCur = pThread;

		if( m_pCur!= nullptr && !m_pCur->isRunning()) {
			m_pCur->start();
		}
	}

	template<typename T>
	inline void SingleThreadExecutor<T>::shutdown() {
		schedule(nullptr);
		schedule(nullptr);
	}

}

#endif //CAPTURE_WORKERTHREAD_H
