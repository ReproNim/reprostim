#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureThreading.h"
#include <catch2/catch.hpp>

using namespace reprostim;

using TestWorkerThread = WorkerThread<std::string>;
using TestSingleThreadExecutor = SingleThreadExecutor<TestWorkerThread>;

// override TestWorkerThread::run implementation
template<>
void TestWorkerThread::run() {
	_INFO("run() enter");
	while (true) {
		if( isTerminated() ) {
			_INFO("terminated " << m_params);
			break;
		}
		_INFO("running... " << m_params);
		SLEEP_MS(30);
	}
	_INFO("run() leave");
}

// test TestWorkerThread
TEST_CASE("TestCaptureThreading_WorkerThread",
		  "[capturelib][CaptureThreading][WorkerThread]") {
	std::string params = "worker_"+getTimeStr();
	TestWorkerThread* p = TestWorkerThread::newInstance(params);
	REQUIRE(p->isRunning() == false);
	REQUIRE(p->isTerminated() == false);
	p->start();
	REQUIRE(p->isRunning() == true);
	REQUIRE(p->isTerminated() == false);
	p->stop();
	REQUIRE(p->isRunning() == false);
	REQUIRE(p->isTerminated() == true);
	TestWorkerThread::deleteInstance(p);
}

// test TestSingleThreadExecutor
TEST_CASE("TestCaptureThreading_SingleThreadExecutor",
		  "[capturelib][CaptureThreading][SingleThreadExecutor]") {
	TestSingleThreadExecutor executor;
	TestWorkerThread* pA = TestWorkerThread::newInstance("workerA_"+getTimeStr());
	TestWorkerThread* pB = TestWorkerThread::newInstance("workerB_"+getTimeStr());

	executor.schedule(pA);
	REQUIRE(pA->isRunning() == true);
	REQUIRE(pA->isTerminated() == false);

	executor.schedule(pB);
	REQUIRE(pA->isRunning() == false);
	REQUIRE(pA->isTerminated() == true);
	REQUIRE(pB->isRunning() == true);
	REQUIRE(pB->isTerminated() == false);

	executor.schedule(nullptr);
	REQUIRE(pA->isRunning() == false);
	REQUIRE(pA->isTerminated() == true);
	REQUIRE(pB->isRunning() == false);
	REQUIRE(pB->isTerminated() == true);
}