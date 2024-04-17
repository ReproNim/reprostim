#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureThreading.h"
#include <catch2/catch.hpp>

using namespace reprostim;

using TestWorkerThread = WorkerThread<std::string>;
using TestSingleThreadExecutor = SingleThreadExecutor<TestWorkerThread>;

struct TestTask {
	std::string name;
	long        timeout;
};
_TYPEDEF_TASK_QUEUE(TestTaskQueue, std::string, TestTask);

// override TestWorkerThread::run implementation
template<>
void TestWorkerThread::run() {
	_INFO("run() enter: " << m_params);
	while (true) {
		if( isTerminated() ) {
			_INFO("terminated " << m_params);
			break;
		}
		_INFO("running... " << m_params);
		SLEEP_MS(30);
	}
	_INFO("run() leave: " << m_params);
}

// override TestTaskQueue::doTask implementation
template<>
void TestTaskQueue::doTask(const TestTask &task) {
	_INFO("doTask() enter: " << task.name);
	SLEEP_MS(task.timeout);
	_INFO("doTask() leave: " << task.name);
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

// test TestTaskQueue
TEST_CASE("TestCaptureThreading_TaskQueue",
		  "[capturelib][CaptureThreading][TaskQueue]") {
	TestTaskQueue q("zzz");

	TestTask taskA = {"taskA", 200};
	TestTask taskB = {"taskB", 1000};
	TestTask taskC = {"taskC", 100};

	q.start();
	SLEEP_MS(50);
	REQUIRE(q.isRunning() == true);
	REQUIRE(q.isTerminated() == false);
	REQUIRE(q.isEmpty() == true);

	q.push(taskA);
	SLEEP_MS(1000);
	q.push(taskB);
	q.push(taskC);
	REQUIRE(q.isEmpty() == false);
	SLEEP_MS(2000);
	REQUIRE(q.isEmpty() == true);
	q.stop();
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