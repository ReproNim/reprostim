TARGET_VIDEOCAPTURE := VideoCapture

LOCAL_CFLAGS += -I../Include

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


CLIB =  -lpthread -ldl -ludev -lasound -lv4l2
MWCAPTURE_LIBA = ../Lib/$(ARCH)/libMWCapture.a

all: $(TARGET_VIDEOCAPTURE)

VIDEOCAPTURE_OBJS = ./VideoCapture.o
	
$(TARGET_VIDEOCAPTURE) : $(VIDEOCAPTURE_OBJS) $(MWCAPTURE_LIBA)
	$(CXX) -o $(TARGET_VIDEOCAPTURE) $(VIDEOCAPTURE_OBJS) $(MWCAPTURE_LIBA) $(CLIB)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(LOCAL_CFLAGS) $< -o $*.o

clean:	
	rm -rf  $(TARGET_VIDEOCAPTURE) $(VIDEOCAPTURE_OBJS)

