#ifndef CAPTURE_CAPTUREREST_H
#define CAPTURE_CAPTUREREST_H

#include <string>
#include <nlohmann/json.hpp>

// Provide REST client service and method configuration, and perform REST call
// using libcurl and nlohmann/json for JSON data handling via HTTP/HTTPS.
// Support API key and access token for authorization, and SSL certificates.

namespace reprostim {

	using nlohmann::json;

	// REST client service configuration
	struct RestConfig {
		std::string baseUrl;
		std::string apiKey;
		std::string accessToken;
		bool        verifySslCert;
		int         connTimeoutSec = 3;
		bool        verbose = false;
	};

	// REST client method configuration
	struct RestMethod {
		std::string name;
		std::string url;
		bool        usePost = false;
		std::string contentType = "application/json";
		std::string accept = "application/json";
		json        bodyParams = {};
		json        queryParams = {};
	};

	// REST call result
	struct RestResult {
		long        httpCode;
		std::string data;
		std::string error;
	};

	// Perform generic REST call
	RestResult restCall(const RestConfig &restConfig, const RestMethod &restMethod);
}

#endif //CAPTURE_CAPTUREREST_H
