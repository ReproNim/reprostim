#ifndef CAPTURE_CAPTUREREPROMON_H
#define CAPTURE_CAPTUREREPROMON_H

#include <unistd.h>
#include <nlohmann/json.hpp>
#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureThreading.h"
#include "reprostim/CaptureRest.h"

// Specifies repromon message level IDs
#define REPROMON_INFO 1
#define REPROMON_WARNING 2
#define REPROMON_ERROR 3

namespace reprostim {
	using json = nlohmann::json;

	// repromon options from config.yaml repromon_opts:
	struct RepromonOpts {
		bool enabled = false;
		std::string api_base_url;
		std::string api_key;
		bool verify_ssl_cert = true;
		//
		int data_provider_id;
		int device_id;
		int message_category_id;
		int message_level_id;
	};

	// repromon parameters passed and available in queue message thread context
	struct RepromonParams {
		const RepromonOpts opts;
	};

	// Specifies a repromon message to be sent to the repromon REST API
	struct RepromonMessage {
		int          level;
		std::string  description;
		json         payload;
		std::string  study;
		std::string  event_on;
		std::string  registered_on;
	};

	// Repromon message queue
	_TYPEDEF_TASK_QUEUE(RepromonQueue, RepromonParams, RepromonMessage);

	// Queue message handler
	void repromonQueueDoTask(RepromonQueue &queue, const RepromonMessage &msg);

	// override RepromonQueue::doTask implementation
	template<>
	inline void RepromonQueue::doTask(const RepromonMessage &msg) {
		repromonQueueDoTask(*this, msg);
	}

} // reprostim
#endif //CAPTURE_CAPTUREREPROMON_H
