# Notes for `ffmpeg` `VA-API` HW encodings

# Overview
Research notes for possible `ffmpeg` configurations suggested
in [#169](https://github.com/ReproNim/reprostim/issues/169).

As part of research did three tests with `ffmpeg`:
 - `raw` - just manual `ffmpeg` command to record video for 30 sec and see how things are going
 - `libx264` - default software H.264 encoding with optimization we have now @ reproiner. Recorded video with the latest reprostim-videocapture utility and manually plugged in/out HDMI cable for 30 sec from the Dune media player FullHD video signal.
 - `h264_vaapi` - hardware accelerated H.264 encoding with VA-API support. Recorded video with the latest reprostim-videocapture utility and manually plugged in/out HDMI cable for 30 sec from the Dune media player FullHD video signal.

Audio was recorded from the HDMI input (rather than in reproiner line-in?), so subdevice ,0 was explicitly specified in the `config.yaml`:
```yaml
ffm_opts:
  a_dev: "hw:1,0"
```

## raw
Original reprostim-videocapture script:
```bash
ffmpeg -f alsa -ac 2 -thread_queue_size 4096 -i hw:1,0 -f v4l2 -input_format yuyv422 -framerate 60 -video_size 1920x1080 -thread_queue_size 4096 -i /dev/video2 -c:v libx264 -flush_packets 1 -preset ultrafast -crf 18 -tune zerolatency -b:v 8M -maxrate 8M -bufsize 16M -vf setpts=PTS-STARTPTS  -threads 4 -acodec aac -af asetpts=PTS-STARTPTS ./Videos/2025/08/2025.08.05-16.54.34.392--.mkv 2>&1
```
Video device: `/dev/video2`
Audio device: `hw:1,0`

Now execute it as a standalone script and record only 30 sec video:
```bash
ffmpeg -f alsa -ac 2 -thread_queue_size 4096 -i hw:1,0 -f v4l2 -input_format yuyv422 -framerate 60 -video_size 1920x1080 -thread_queue_size 4096 -i /dev/video2 -c:v libx264 -flush_packets 1 -preset ultrafast -crf 18 -tune zerolatency -b:v 8M -maxrate 8M -bufsize 16M -vf setpts=PTS-STARTPTS  -threads 4 -acodec aac -af asetpts=PTS-STARTPTS -t 30 "./$(date +%Y.%m.%d-%H.%M.%S).mkv" 2>&1
```
Result file: `raw/2025.08.05-17.34.41.mkv`

```bash
ffmpeg -f alsa -ac 2 -thread_queue_size 4096 -i hw:1,0 -f v4l2 -input_format yuyv422 -framerate 60 -video_size 1920x1080 -thread_queue_size 4096 -i /dev/video2 -vaapi_device /dev/dri/renderD128 -vf 'format=nv12,hwupload,setpts=PTS-STARTPTS' -c:v h264_vaapi -acodec aac -af asetpts=PTS-STARTPTS -t 30 "./$(date +%Y.%m.%d-%H.%M.%S).mkv" 2>&1
```

Result file: `raw/2025.08.05-17.46.21.mkv`, `raw/2025.08.05-17.55.04.mkv`

## libx264

Just default video+audio recorded by reprostim-videocapture with software CPU-based H.264
encoder: `libx264/Videos/2025/08/2025.08.05-18.13.53.426--2025.08.05-18.14.25.750.mkv`

## h264_vaapi

My dev machine missed HEVC support, so I had to use H.264 VA-API encoding. I was able successfully to record both
video and audio with H.264+VA-API encoding.

The following changes were applied to the reprostim-videocapture `config.yaml`:
```yaml
ffm_opts:
  # explicitly specify an audio HDMI input sub-device from my Magewell USB capture device
  # optionally it can be specified as "auto,0", but for research purposes I used hardcoded "hw:1,0"
  a_dev: "hw:1,0"

  # specify h264 VA-API encoding options and timing opts
  v_enc: "-vaapi_device /dev/dri/renderD128 -vf 'format=nv12,hwupload,setpts=PTS-STARTPTS' -c:v h264_vaapi"
  # don't specify threads, as it is not supported by VA-API
  n_threads: ""
```

Video+audio recorded by reprostim-videocapture : `h264_vaapi/Videos/2025/08/2025.08.05-18.19.28.273--2025.08.05-18.20.00.046.mkv`

# Results

I was able to record video with both `libx264` and `h264_vaapi` encodings. The `h264_vaapi` encoding was successful,
and the resulting file was playable without issues by VLC and contains audio as well.

CPU usage for `h264_vaapi` encoding was 2x times lower than for `libx264`,
which is expected due to hardware acceleration:

### CPU Usage (%pcpu) Comparison: libx264 vs h264_vaapi

| libx264, %CPU | h264_vaapi, %CPU |
|---------------|------------------|
| 200.0         | 100.0            |
| 96.9          | 60.5             |
| 91.0          | 46.6             |
| 86.5          | 46.2             |
| 84.1          | 45.4             |
