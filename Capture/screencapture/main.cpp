#include <sysexits.h>
#include <unistd.h>
#include "ScreenCapture.h"

////////////////////////////////////////////////////////////////////////////
// Entry point

int main(int argc, char* argv[]) {
	int res = EX_OK;
	do {
		ScreenCaptureApp app;
		res = app.run(argc, argv);
		optind = 0; // force restart argument scanning for getopt
	} while( res==EX_CONFIG_RELOAD );
	return res;
}

