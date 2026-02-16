# Notes for `split-video` command

## Buffer Layout

The `split-video` command extracts a segment from a source video file.
The selected segment is defined by `orig_offset` and `duration`. An output
video is produced with additional padding: `buffer_before` seconds
prepended and `buffer_after` seconds appended around the selection.

The diagram below illustrates how the buffer and selection regions
map onto the source video timeline:

```{mermaid}
%%{init: {'theme': 'default', 'themeVariables': {'critBkgColor': '#4CAF50', 'critBorderColor': '#2E7D32', 'critTextColor': '#ffffff', 'activeTaskBkgColor': '#FEFBD0', 'activeTaskBorderColor': '#808080'}}}%%
gantt
    title Buffer Layout in split-video 
    dateFormat YYYY-MM-DD HH:mm:ss
    axisFormat %M:%S
    tickInterval 120second

    section Source <br>Original <br>Video
    ‎                                     :done, v0, 2024-01-01 00:00:00, 2024-01-01 00:00:00
    Entire video file                       :done, v1, 2024-01-01 00:00:00, 2024-01-01 00:12:00
    ‎                                     :done, v2, 2024-01-01 00:00:00, 2024-01-01 00:00:00

    section Output <br>Video<br>with Buffers
    ‎                                     :o0, 2024-01-01 00:00:00, 2024-01-01 00:00:00
    buffer_duration = 315.5s                :o1, 2024-01-01 00:03:20, 2024-01-01 00:08:36
    ‎                                     :o2, 2024-01-01 00:00:00, 2024-01-01 00:00:00

    section Buffer <br>Details
    ‎                                     :b0, 2024-01-01 00:00:00, 2024-01-01 00:00:00
    orig_buffer_offset = 200.0s             :active, o0, 2024-01-01 00:00:00, 2024-01-01 00:03:20
    buffer_before = 10.0s                   :b1, 2024-01-01 00:03:20, 2024-01-01 00:03:30
    orig_offset = 210.0s                    :active, o2, 2024-01-01 00:00:00, 2024-01-01 00:03:30
    Actual video (duration = 303.0s)        :crit, s1, 2024-01-01 00:03:30, 2024-01-01 00:08:33
    buffer_after = 2.5s                     :b2, 2024-01-01 00:08:33, 2024-01-01 00:08:36
    ‎                                     :b3, 2024-01-01 00:00:00, 2024-01-01 00:00:00

```

### Sidecar fields

The `split-video` command produces a `.split-video.jsonl` sidecar file
with the following fields:

| Field                | Description                                                 |
|----------------------|-------------------------------------------------------------|
| `orig_offset`        | Start of the selected segment in the source video (seconds) |
| `duration`           | Length of the selected segment (seconds)                    |
| `start`              | Start timecode of the selected segment (`HH:MM:SS.mmm`)     |
| `end`                | End timecode of the selected segment                        |
| `buffer_before`      | Padding prepended before the selection (seconds)            |
| `buffer_after`       | Padding appended after the selection (seconds)              |
| `orig_buffer_offset` | Start of the output segment in the source video (seconds)   |
| `buffer_duration`    | Total length of the output segment (seconds)                |
| `buffer_start`       | Start timecode of the output segment                        |
| `buffer_end`         | End timecode of the output segment                          |
| `video_resolution`   | Resolution of the source video                              |
| `video_rate_fps`     | Frame rate of the source video                              |
| `video_size_mb`      | Size of the output video file (MB)                          |
| `video_rate_mbpm`    | Video bitrate (MB per minute)                               |
| `audio_info`         | Audio stream description                                    |

### Example sidecar

```json
{
  "buffer_before": 10.0,
  "buffer_after": 2.5,
  "buffer_start": "00:03:20.001",
  "buffer_end": "00:08:35.501",
  "buffer_duration": 315.5,
  "orig_buffer_offset": 200.001,
  "start": "00:03:30.001",
  "end": "00:08:33.001",
  "duration": 303.0,
  "offset": 210.001,
  "video_resolution": "1920x1080",
  "video_rate_fps": 25.0,
  "video_size_mb": 367.8,
  "video_rate_mbpm": 9.3,
  "audio_info": "48000Hz 16b 2ch pcm_s16le"
}
```