#!/bin/bash

#set VDEV=/dev/video1
#set MKV=./1.mkv

#echo "Test 1"

#rm $MKV
#ffmpeg -f v4l2 -input_format yuyv422 -framerate 60 -video_size 1920x1080 -thread_queue_size 40960 -i $VDEV -c:v libx264 -flush_packets 1 -an $MKV

#ffmpeg -f alsa -ac 2 -thread_queue_size 4096 -i hw:1,1
 # -f v4l2 -input_format yuyv422 -framerate 60 -video_size 1920x1080 -thread_queue_size 4096
 # -i /dev/video0 -c:v libx264 -flush_packets 1
 # -acodec aac ./1.mkv 2>&1

# Simple 15 sec video capture with no audio
#echo "Test 001"
#rm output001.mp4
#/usr/bin/time -v ffmpeg -f v4l2 -framerate 60 -video_size 1920x1080 -t 15 -i /dev/video0 -an output001.mp4

# Simple 15 sec video capture with no audio and x264 codec
#echo "Test 002"
#rm output002.mp4
#/usr/bin/time -v ffmpeg -f v4l2 -framerate 60 -video_size 1920x1080 -t 15 -i /dev/video0 -c:v libx264 -an output002.mp4

# Simple video capture with audio and video and start time set to 0 for both audio and video
#echo "Test 003"
#rm output003.mp4
#ffmpeg -f alsa -ac 2 -thread_queue_size 4096 -i hw:1,1 -f v4l2 -framerate 60 -video_size 1920x1080 -i /dev/video0 -c:v libx264 -acodec aac -vf setpts=PTS-STARTPTS -af asetpts=PTS-STARTPTS output003.mp4

# video capture with x264 optimizations: fast 2M bit rate
#echo "Test 004"
#rm output004.mp4
#/usr/bin/time -v ffmpeg -f alsa -t 15 -ac 2 -thread_queue_size 4096 -i hw:1,1 -f v4l2 -t 15 -framerate 60 -video_size 1920x1080 -i /dev/video0 -c:v libx264 -b:v 2M -preset fast -acodec aac -vf setpts=PTS-STARTPTS -af asetpts=PTS-STARTPTS output004.mp4

# video capture with x264 optimizations: ultrafast
#echo "Test 005"
#rm output005.mp4
#/usr/bin/time -v ffmpeg -f alsa -t 15 -ac 2 -thread_queue_size 4096 -i hw:1,1 -f v4l2 -t 15 -framerate 60 -video_size 1920x1080 -i /dev/video0 -c:v libx264 -b:v 2M -preset ultrafast -acodec aac -vf setpts=PTS-STARTPTS -af asetpts=PTS-STARTPTS output005.mp4

# video capture with x264 optimizations: ultrafast, crf=18 r-60?
#echo "Test 006"
#rm output006.mp4
#/usr/bin/time -v ffmpeg -f alsa -t 15 -ac 2 -thread_queue_size 4096 -i hw:1,1 -f v4l2 -t 15 -framerate 60 -video_size 1920x1080 -i /dev/video0 -c:v libx264 -r 60 -b:v 2M -preset ultrafast -crf 18 -acodec aac -vf setpts=PTS-STARTPTS -af asetpts=PTS-STARTPTS output006.mp4

# video capture with x264 optimizations: ultrafast, crf=18 zerolatency
# 470M/hour
#echo "Test 007"
#rm output007.mp4
#/usr/bin/time -v ffmpeg -f alsa -t 600 -ac 2 -thread_queue_size 4096 -i hw:1,1 -f v4l2 -t 600 -framerate 60 -video_size 1920x1080 -i /dev/video0 -c:v libx264 -flush_packets 1 -preset ultrafast -crf 18 -r 60 -tune zerolatency -b:v 2M -maxrate 2M -bufsize 4M  -acodec aac -vf setpts=PTS-STARTPTS -af asetpts=PTS-STARTPTS output007.mp4

# video capture with x264 optimizations: ultrafast, crf=18 zerolatency
#echo "Test 008"
#rm output008.mp4
#/usr/bin/time -v ffmpeg -f alsa -t 15 -ac 2 -thread_queue_size 4096 -i hw:1,1 -f v4l2 -t 15 -framerate 60 -video_size 1920x1080 -i /dev/video0 -c:v libx264 -flush_packets 1 -preset ultrafast -crf 18 -r 60 -tune zerolatency -b:v 2M -maxrate 2M -bufsize 4M  -acodec aac -vf setpts=PTS-STARTPTS -af asetpts=PTS-STARTPTS output008.mp4

# video capture similar to initial one we have before changes
echo "Test 009"
rm output009.mp4
/usr/bin/time -v ffmpeg -f alsa -t 15 -ac 2 -thread_queue_size 4096 -i hw:1,1 -f v4l2 -t 15 -input_format yuyv422 -framerate 60 -video_size 1920x1080 -thread_queue_size 4096 -i /dev/video0 -c:v libx264 -flush_packets 1 output009.mkv
