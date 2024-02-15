#include <sysexits.h>
#include <unistd.h>
#include "ScreenCapture.h"

////////////////////////////////////////////////////////////////////////////
// Entry point

int main(int argc, char* argv[]) {
	return mainImpl<ScreenCaptureApp>(argc, argv);
}

