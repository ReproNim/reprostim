ARCH=`uname -m`
CFLAGS="-O2 \
          -Wall \
          -Wextra \
          -Wno-unused-parameter \
          -Wno-sign-compare \
          -Wno-unused-variable \
          -Wno-unused-but-set-variable \
          -Wno-missing-field-initializers  \
          -fPIC" $CFLAGS

if [ "$ARCH" = "x86_64" ];
then
ARCH=x64
else if [ "$ARCH" = "i386" ]
then
CFLAGS="-m32 $CFLAGS"
else if [ "$ARCH" = "i686" ]
then
CFLAGS="-m32 $CFLAGS"
ARCH=i386
else if [ "$ARCH" = "aarch64" ]
then
ARCH=arm64
fi
fi
fi
fi

#ITRD_USB = ../../3rdpart/libusb/lib/linux/$ARCH/libusb-1.0.a
CLIB="-lpthread -ldl -ludev -lasound -lv4l2"

rm -rf temp
mkdir temp
cd temp
ar x ../$ARCH/libMWCapture.a
g++ -shared -fPIC $CFLAGS -o ../$ARCH/libMWCapture.so *.o $CLIB
strip ../$ARCH/libMWCapture.so
cd ../

rm -rf temp
mkdir temp
cd temp
ar x ../$ARCH/libmwcc708decoder.a
g++ -shared -fPIC $CFLAGS -o ../$ARCH/libmwcc708decoder.so *.o
strip ../$ARCH/libmwcc708decoder.so
cd ../

rm -rf temp
mkdir temp
cd temp
ar x ../$ARCH/libmwcc708render.a
g++ -shared -fPIC $CFLAGS -o ../$ARCH/libmwcc708render.so *.o
strip ../$ARCH/libmwcc708render.so
cd ../

rm -rf temp
mkdir temp
cd temp
ar x ../$ARCH/libmw_mp4.a
#ar x ../../3rdpart/libusb/lib/linux/$ARCH/libusb-1.0.a
g++ -shared -fPIC $CFLAGS -o ../$ARCH/libmw_mp4.so *.o  $CLIB
strip ../$ARCH/libmw_mp4.so
cd ../

rm -rf temp
mkdir temp
cd temp
ar x ../$ARCH/libmw_venc.a
#ar x ../../3rdpart/libusb/lib/linux/$ARCH/libusb-1.0.a
g++ -shared -fPIC $CFLAGS -o ../$ARCH/libmw_venc.so *.o  $CLIB
strip ../$ARCH/libmw_venc.so
cd ../
