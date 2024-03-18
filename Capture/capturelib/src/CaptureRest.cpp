#include <nlohmann/json.hpp>
#include <curl/curl.h>
#include "reprostim/CaptureLib.h"
#include "reprostim/CaptureRest.h"

using json = nlohmann::json;

namespace reprostim {

	inline std::string url_escape(CURL *curl, const std::string &s) {
		if (curl) {
			char *output = curl_easy_escape(curl, s.c_str(), s.length());
			if (output) {
				std::string escaped = output;
				curl_free(output);
				return escaped;
			}
		}
		return s;
	}

	// Callback function for libcurl to write response data
	static size_t restWriteCallback(char *ptr, size_t size, size_t nmemb, std::string *data) {
		data->append(ptr, size * nmemb);
		return size * nmemb;
	}

	RestResult restCall(const RestConfig &restConfig, const RestMethod &restMethod) {
		RestResult rr = { 0, "", "" };
		CURL *curl = nullptr;
		struct curl_slist *headers = nullptr;
		std::string url = "";
		_VERBOSE("Rest call: " << restConfig << ", " << restMethod);
		try {
			curl = curl_easy_init();

			if (curl) {
				if( !restMethod.contentType.empty() ) {
					headers = curl_slist_append(headers, ("Content-Type: " + restMethod.contentType).c_str());
				}

				if( !restMethod.accept.empty() ) {
					headers = curl_slist_append(headers, ("Accept: " + restMethod.accept).c_str());
				}

				// Set authorization header if ACCESS_TOKEN or API_KEY is available
				std::string auth_header;
				if( !restConfig.accessToken.empty() ) {
					auth_header = "Authorization: Bearer " + restConfig.accessToken;
				} else if ( !restConfig.apiKey.empty() ) {
					auth_header = "X-Api-Key: " + restConfig.apiKey;
				}

				if (!auth_header.empty()) {
					headers = curl_slist_append(headers, auth_header.c_str());
				}

				// build url
				std::ostringstream ourl;
				ourl << restConfig.baseUrl << restMethod.url;

				if( !restMethod.queryParams.empty() ) {
					for( auto it = restMethod.queryParams.begin(); it!=restMethod.queryParams.end(); ++it ) {
						if( it!=restMethod.queryParams.begin() ) {
							ourl << "&";
						} else {
							ourl << "?";
						}
						ourl << it.key() << "=" << url_escape(curl, it.value());
					}
				}

				url = ourl.str();
				_VERBOSE("Rest url: " << url);

				// Configure libcurl options
				curl_easy_setopt(curl, CURLOPT_URL, url.c_str());

				// Set connection timeout
				if(restConfig.connTimeoutSec > 0 ) {
					curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, restConfig.connTimeoutSec);
					curl_easy_setopt(curl, CURLOPT_TIMEOUT, restConfig.connTimeoutSec);
				}

				if( restConfig.verbose ) {
					curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
				}

				// use POST
				if( restMethod.usePost ) {
					curl_easy_setopt(curl, CURLOPT_POST, 1L);
				}

				// Set SSL certificate verification
				if (!restConfig.verifySslCert) {
					curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
					curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
				}

				// set post data if any
				if( restMethod.usePost ) {
					std::string postData = "";
					if( !restMethod.bodyParams.empty() ) {
						postData = restMethod.bodyParams.dump();
					}
					curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str());
				}

				curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
				curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, restWriteCallback);
				std::string response_data;
				curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);

				// Perform HTTP POST request
				CURLcode res = curl_easy_perform(curl);
				if (res == CURLE_OK) {
					long httpCode = 0;
					curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
					rr.httpCode = httpCode;
					if (httpCode == 200) {
						_VERBOSE("Rest method \"" << restMethod.name << "\" executed successfully");
						rr.data = response_data;
					} else {
						rr.error = "Rest method \"" + restMethod.name + "\" failed, HTTP status code: " +
								   std::to_string(httpCode) + ", response: " + response_data;
						rr.data = response_data;
					}
				} else {
					rr.error = "Rest method \"" + restMethod.name +
							   "\" HTTP request failure: " + curl_easy_strerror(res);
				}
			}
		} catch (const std::exception &ex) {
			rr.error = "Rest method \"" + restMethod.name +
					   "\" unhandled error: " + ex.what();
		}

		// cleanup
		if( headers ) {
			curl_slist_free_all(headers);
			headers = nullptr;
		}

		if( curl ) {
			curl_easy_cleanup(curl);
			curl = nullptr;
		}

		_VERBOSE("Rest call result: " << rr);

		if( !rr.error.empty() ) {
			_ERROR(rr.error);
			_ERROR("  - " << rr);
			_ERROR("  - url=" << url);
			_ERROR("  - " << restConfig);
			_ERROR("  - " << restMethod);
		}
		return rr;
	}

}