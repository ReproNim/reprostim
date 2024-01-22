#ifndef REPROSTIM_CAPTURELIB_H
#define REPROSTIM_CAPTURELIB_H

/*########################### Common macros ############################*/

#ifndef _ERROR
#define _ERROR(expr) std::cerr << expr << std::endl
#endif

#ifndef _INFO
#define _INFO(expr) std::cout << expr << std::endl
#endif

#ifndef _INFO_RAW
#define _INFO_RAW(expr) std::cout << expr
#endif

#ifndef _VERBOSE
#define _VERBOSE(expr) if( verbose ) { std::cout << expr << std::endl; }
#endif

#ifndef PATH_MAX_LEN
#define PATH_MAX_LEN 1024
#endif

#ifndef SLEEP_MS
#define SLEEP_MS(sec) std::this_thread::sleep_for(std::chrono::milliseconds(sec))
#endif

#ifndef SLEEP_SEC
#define SLEEP_SEC(sec) SLEEP_MS(static_cast<int>(sec*1000))
#endif


#endif //REPROSTIM_CAPTURELIB_H
