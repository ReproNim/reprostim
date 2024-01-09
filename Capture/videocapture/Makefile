TARGET_VIDEOCAPTURE := reprostim-videocapture

LOCAL_CFLAGS += -I../3rdparty/MWCapture_SDK_Linux-3_3_1_1313/Include

CC = gcc
CXX = g++
LD = ld

CFLAGS += -O0 \
          -Wall \
          -Wextra \
          -Wno-unused-parameter \
          -Wno-sign-compare \
          -Wno-unused-variable \
          -Wno-unused-but-set-variable \
          -Wno-missing-field-initializers  \
          -fPIC \
	  -std=c++17 \
	  -g \
	  $(LOCAL_CFLAGS) \
	  

ARCH:=$(shell uname -m)

ifeq ($(ARCH),x86_64)
override ARCH = x64
endif

ifeq ($(ARCH),i386)
CFLAGS += -m32
endif

ifeq ($(ARCH),i686)
CFLAGS += -m32
override ARCH = i386
endif

ifeq ($(ARCH),aarch64)
override ARCH = arm64
endif


CLIB =  -lpthread -ldl -ludev -lasound -lv4l2 -lyaml-cpp
MWCAPTURE_LIBA = ../3rdparty/MWCapture_SDK_Linux-3_3_1_1313/Lib/$(ARCH)/libMWCapture.a

all: $(TARGET_VIDEOCAPTURE)

VIDEOCAPTURE_OBJS = ./VideoCapture.o
	
$(TARGET_VIDEOCAPTURE) : $(VIDEOCAPTURE_OBJS) $(MWCAPTURE_LIBA)
	$(CXX) -o $(TARGET_VIDEOCAPTURE) $(VIDEOCAPTURE_OBJS) $(MWCAPTURE_LIBA) $(CLIB)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(LOCAL_CFLAGS) $< -o $*.o

clean:	
	rm -rf  $(TARGET_VIDEOCAPTURE) $(VIDEOCAPTURE_OBJS)

