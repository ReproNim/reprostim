#include "reprostim/CaptureRepromon.h"
#include "reprostim/CaptureRest.h"

using json = nlohmann::json;

namespace reprostim {

	// Call MessageService/send_message REST API to notify repromon
	void repromonSendMessage(
			const RestConfig &cfg,
			const std::string &study,
			int category,
			int level,
			int device,
			int provider,
			const std::string &description,
			const json &payload,
			const std::string &event_on,
			const std::string &registered_on
	) {
		RestMethod rm = {
				"repromonSendMessage",
				"/message/send_message",
				true,
				"application/json",
				"application/json",
				{},
				// obligatory query params
				{
						{"category", std::to_string(category)},
						{"level", std::to_string(level)},
						{"device", std::to_string(device)},
						{"provider", std::to_string(provider)},
						{"description", description}
				}
		};

		json& params = rm.queryParams;

		// add optional params
		if( !study.empty() ) { params.push_back({"study", study}); }
		if( !payload.empty() ) { params.push_back({"payload", payload.dump()}); }
		if( !event_on.empty() ) { params.push_back({"event_on", event_on}); }
		if( !registered_on.empty() ) { params.push_back({"registered_on", registered_on}); }

		RestResult rr = restCall(cfg, rm);
	}

	// Queue message handler implementation
	void repromonQueueDoTask(RepromonQueue &queue, const RepromonMessage &msg) {
		_VERBOSE("RepromonQueue::doTask() enter: ");
		_INFO("Repromon message: "
					  << "api_base_url=" << queue.getParams().opts.api_base_url
					  << ", description=" << msg.description
					  << ", payload=" << msg.payload
					  << ", ...");
		if( msg.level<queue.getParams().opts.message_level_id ) {
			_VERBOSE("Repromon message: skip level=" << std::to_string(msg.level));
		}

		RestConfig cfg = {
				queue.getParams().opts.api_base_url,
				queue.getParams().opts.api_key,
				"",
				queue.getParams().opts.verify_ssl_cert
		};

		repromonSendMessage(cfg,
				msg.study,
				queue.getParams().opts.message_category_id,
				queue.getParams().opts.message_level_id,
				queue.getParams().opts.device_id,
				queue.getParams().opts.data_provider_id,
				msg.description,
				msg.payload,
				msg.event_on,
				msg.registered_on
		);
		_VERBOSE("RepromonQueue::doTask() leave: ");
	}
}