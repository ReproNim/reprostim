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

		friend std::ostream& operator<<(std::ostream& os, const RestConfig& cfg);
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

		friend std::ostream& operator<<(std::ostream& os, const RestMethod& method);
	};

	// REST call result
	struct RestResult {
		long        httpCode;
		std::string data;
		std::string error;

		friend std::ostream& operator<<(std::ostream& os, const RestResult& rr);
	};

	// Perform generic REST call
	RestResult restCall(const RestConfig &restConfig, const RestMethod &restMethod);

	// inline ostream operator for RestConfig
	inline std::ostream& operator<<(std::ostream& os, const RestConfig& cfg) {
		os << "RestConfig(baseUrl=" << cfg.baseUrl <<
			", apiKey=..." <<
			", accessToken=..." <<
			", verifySslCert=" << cfg.verifySslCert <<
			", connTimeoutSec=" << cfg.connTimeoutSec <<
			", verbose=" << cfg.verbose << ")";
		return os;
	}

	// inline ostream operator for RestMethod
	inline std::ostream& operator<<(std::ostream& os, const RestMethod& method) {
		os << "RestMethod(name=" << method.name <<
			", url=" << method.url <<
			", usePost=" << method.usePost <<
			", contentType=" << method.contentType <<
			", accept=" << method.accept <<
			", bodyParams=" << method.bodyParams <<
			", queryParams=" << method.queryParams << ")";
		return os;
	}

	// inline ostream operator for RestResult
	inline std::ostream& operator<<(std::ostream& os, const RestResult& rr) {
		os << "RestResult(httpCode=" << rr.httpCode <<
			", data=" << rr.data <<
			", error=" << rr.error << ")";
		return os;
	}
}

#endif //CAPTURE_CAPTUREREST_H
