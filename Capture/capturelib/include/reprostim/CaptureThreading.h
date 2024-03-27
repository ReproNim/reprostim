#ifndef CAPTURE_WORKERTHREAD_H
#define CAPTURE_WORKERTHREAD_H

#include <iostream>
#include <atomic>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include "reprostim/CaptureLib.h"

//////////////////////////////////////////////////////////////////////////
// Macros

#ifndef _SYNC_LOCK
#define _SYNC_LOCK(mutex_) std::lock_guard<std::mutex> _sync_lock(mutex_)
#endif //_SYNC_LOCK

#ifndef _SYNC_ULOCK
#define _SYNC_ULOCK(mutex_) std::unique_lock<std::mutex> _sync_ulock(mutex_)
#endif //_SYNC_ULOCK

#ifndef _DECLARE_CLASS_WITH_SYNC
#define _DECLARE_CLASS_WITH_SYNC() mutable std::mutex _this_mutex_
#endif //_DECLARE_CLASS_WITH_SYNC

#ifndef _SYNC
#define _SYNC() _SYNC_LOCK(_this_mutex_)
#endif //_SYNC

#ifndef _SYNC_U
#define _SYNC_U() _SYNC_ULOCK(_this_mutex_)
#endif //_SYNC_U

#ifndef _TYPEDEF_TASK_QUEUE
#define _TYPEDEF_TASK_QUEUE(TQueue, TParams, TTask) \
using TQueue = TaskQueue<TParams, TTask>; \
using TQueue##WorkerThread = WorkerThread<TParams, TTask>;\
template<> inline void TQueue##WorkerThread::run() { static_cast<TQueue&>(*this).run(); }
#endif //_TYPEDEF_TASK_QUEUE


namespace reprostim {

	//////////////////////////////////////////////////////////////////////////
	// WorkerThread template

	template<typename T, typename U = void>
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
		static WorkerThread<T, U>* newInstance(const T &params);
		static void deleteInstance(WorkerThread<T, U>* p);
	};

	//////////////////////////////////////////////////////////////////////////
	// WorkerThread Implementation

	template<typename T, typename U>
	WorkerThread<T, U>::WorkerThread(const T &params) : m_params(params) {
		m_running = false;
		m_terminated = false;
	}

	template<typename T, typename U>
	WorkerThread<T, U>::~WorkerThread() {
	}

	template<typename T, typename U>
	inline const T& WorkerThread<T, U>::getParams() const {
		return m_params;
	}

	template<typename T, typename U>
	inline bool WorkerThread<T, U>::isRunning() const {
		return m_running;
	}

	template<typename T, typename U>
	inline bool WorkerThread<T, U>::isTerminated() const {
		return m_terminated;
	}

	template<typename T, typename U>
	void WorkerThread<T, U>::run() {
		// provide own template specialization
		_INFO("WorkerThread::run: not implemented");
	}

	template<typename T, typename U>
	void WorkerThread<T, U>::runInternal() {
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

	template<typename T, typename U>
	void WorkerThread<T, U>::start() {
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

	template<typename T, typename U>
	void WorkerThread<T, U>::stop() {
		m_terminated = true;
		for (int i = 0; i < 10; i++) {
			if (!m_running) {
				break;
			}
			SLEEP_MS(100);
		}
	}

	template<typename T, typename U>
	inline WorkerThread<T, U>* WorkerThread<T, U>::newInstance(const T &params) {
		return new WorkerThread<T, U>(params);
	}

	template<typename T, typename U>
	inline void WorkerThread<T, U>::deleteInstance(WorkerThread<T, U>* p) {
		if( p!= nullptr ) {
			delete p;
		}
	}

	//////////////////////////////////////////////////////////////////////////
	// TaskQueue template

	template<typename T, typename U>
	class TaskQueue : public WorkerThread<T, U>{
		_DECLARE_CLASS_WITH_SYNC();

	protected:
		std::condition_variable m_cond;
		std::queue<U>           m_queue;

		bool tryPop(U& task);

	public:
		TaskQueue(const T& t);

		void doTask(const U &task);
		bool isEmpty() const;
		void push(const U &task);
		void run();
		void stop();
	};

	//////////////////////////////////////////////////////////////////////////
	// TaskQueue implementation

	template<typename T, typename U>
	TaskQueue<T, U>::TaskQueue(const T& t) : WorkerThread<T, U>(t) {
	}

	template<typename T, typename U>
	inline bool TaskQueue<T, U>::tryPop(U& task) {
		_SYNC();
		if( m_queue.empty() ) {
			return false;
		}
		task = m_queue.front();
		m_queue.pop();
		return true;
	}

	template<typename T, typename U>
	void TaskQueue<T, U>::doTask(const U &task) {
		// provide own template specialization
		_INFO("TaskQueue::doTask: not implemented: ");
	}

	template<typename T, typename U>
	inline bool TaskQueue<T, U>::isEmpty() const {
		_SYNC();
		return m_queue.empty();
	}

	template<typename T, typename U>
	inline void TaskQueue<T, U>::push(const U &task) {
		_SYNC();
		m_queue.push(task);
		m_cond.notify_one();
	}

	template<typename T, typename U>
	void TaskQueue<T, U>::run() {
		U task;
		while (true) {
			{
				_SYNC_U();
				// do some periodic check
				m_cond.wait_for(_sync_ulock,
								std::chrono::milliseconds(10*1000),
								[this]() {
									return
										!m_queue.empty() &&
										!this->isTerminated();
								});
			}
			if( this->isTerminated() ) {
				break;
			}
			if( tryPop(task) ) {
				doTask(task);
			}
			// do some sleep
			SLEEP_MS(1);
		}
	}

	template<typename T, typename U>
	inline void TaskQueue<T, U>::stop() {
		WorkerThread<T, U>::m_terminated = true;
		m_cond.notify_one();
		WorkerThread<T, U>::stop();
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
