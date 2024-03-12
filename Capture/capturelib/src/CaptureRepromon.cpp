#include "reprostim/CaptureRepromon.h"
#include <curl/curl.h>
#include <nlohmann/json.hpp>

namespace reprostim {

	// override RepromonTaskQueue::doTask implementation
	template<>
	void RepromonQueue::doTask(const RepromonMessage &msg) {
		_VERBOSE("RepromonQueue::doTask() enter: ");
		_INFO("Repromon message: "
					  << "api_base_url=" << m_params.opts.api_base_url
					  << ", description=" << msg.description
					  << ", payload=" << msg.payload
					  << ", ...");
		_VERBOSE("RepromonQueue::doTask() leave: ");
	}

}