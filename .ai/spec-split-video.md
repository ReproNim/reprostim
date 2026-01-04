# Video Split Tool Specification

## Overview

The `split-video` command is a utility to extract specific time segments from recorded video files, creating sliced output files with precise timing information and metadata.

Script (ideally in python) should take:

- location of not sliced videos
- beginning absolute time parameter
- end time or duration parameter
- optional "parameters" of how much of "buffer" to take before/after video begins/ends so we could account for time imprecision
  - all durations should accept either simple float for seconds (e.g. 121) , or ISO 8601 duration (`P2M1S`. note: isodurations does not take this value - wants a date! odd)
  - precision of `ms` is enough
  - if buffers go outside of the video times -- trim to video (so to 0 on the left, and total length on the right) and store (see below) actual values in the .json
  - if video itself doesn't overlap fully with desired time/duration -- for now just error
    - specific case: it was multiple (more than 1 video) videos captured for the single desired time duration -- we do not bother ATM to somehow join them.
- output .mkv filename.
  - in addition to .mkv generate or update (if exists) side car  .json file with annotation of the parameters etc provided into "reprostim-videocapture" field. Should contain "onset" (ISO 8601 time, no date), "duration", "buffer-before", "buffer-after" in seconds (up to .ms), all reprostim-videocapture metadata from the log (https://github.com/ReproNim/reprostim/issues/83) .
  - Do not store absolute dates anywhere. Times are ok, not dates

example:

```shell
reprostim split-video --buffer-before 10 --buffer-after 10 --start 2024-02-02T17:30:00 --duration P3M  --input $VIDEOS/2024.02.02.17.20.38.680_2024.02.02.17.20.44.774.mkv --output $BIDS/sub-01/func/sub-01_task-rest_bold.mkv
```

```shell
reprostim split-video --buffer-before 5 --buffer-after 5 --start 2025-11-05T14:03:30 --duration PT5M07S  --input temp/Videos/2025/11/2025.11.05-14.03.28.837--2025.11.05-14.13.47.757.mkv --output temp/test_split1.mkv

```

in case of input filename not satisfying the pattern to have starting time -- error


`split-video` which could be used independently of the overall setup with videos.tsv etc. Should take specification 
for splitting, template for output filename(s), and overloads on command line (like buffer durations). It should have 
option to produce .json file with result records depicting exact buffers etc durations (e.g. if we specified buffer 
of 10 sec, but start from 2nd second, we could have only 2 seconds buffer in the beginning). Maybe add an 
option `--buffer-policy=strict|flexible` so if strict, would error out if buffer cannot be fulfilled:
   - likely might be just a wrapper around `ffmpeg` invocation
   - input specification should have set of records with starttime, endtime, filename template which could potentially embed all those + extra metadata field in the record like `title`  or some other.
   - think about it to be used to produce files for a BIDS dataset (next command), so filename pattern would be to be placed into a BIDS dataset, see https://github.com/bids-standard/bids-specification/pull/2022
   - think also that this tool could potentially be used to cut up a longer video into shorter ones, like was done for full conference sessions on distribits: https://hub.datalad.org/distribits/recordings/src/branch/master/code/video_job.sh
