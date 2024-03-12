#ifndef CAPTURE_CAPTUREREPROMON_H
#define CAPTURE_CAPTUREREPROMON_H

#include <unistd.h>
#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureThreading.h"

namespace reprostim {

	// repromon options from config.yaml repromon_opts:
	struct RepromonOpts {
		bool enabled = false;
		std::string api_base_url;
		std::string api_key;
		int data_provider_id;
		int device_id;
		int message_category_id;
		int message_level_id;
	};

	struct RepromonParams {
		const RepromonOpts opts;
	};

	struct RepromonMessage {
		std::string description;
		std::string payload;
		std::string event_on;
		std::string registered_on;
		std::string study;
	};

	_TYPEDEF_TASK_QUEUE(RepromonQueue, RepromonParams, RepromonMessage);


} // reprostim
#endif //CAPTURE_CAPTUREREPROMON_H
