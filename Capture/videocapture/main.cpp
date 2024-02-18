#include <sysexits.h>
#include <unistd.h>
#include "VideoCapture.h"

////////////////////////////////////////////////////////////////////////////
// Entry point

int main(int argc, char* argv[]) {
	return mainImpl<VideoCaptureApp>(argc, argv);
}
