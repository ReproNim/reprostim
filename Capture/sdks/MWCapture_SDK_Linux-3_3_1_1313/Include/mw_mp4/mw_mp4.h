////////////////////////////////////////////////////////////////////////////////
// CONFIDENTIAL and PROPRIETARY software of Magewell Electronics Co., Ltd.
// Copyright (c) 2011-2020 Magewell Electronics Co., Ltd. (Nanjing)
// All rights reserved.
// This copyright notice MUST be reproduced on all authorized copies.
////////////////////////////////////////////////////////////////////////////////

#ifndef MW_MP4_H
#define MW_MP4_H

#include <stdint.h>
#if !defined( _WIN32 )
#include <stdbool.h>
#endif

#ifdef _WIN32
#ifdef MW_MP4_EXPORTS
#define MW_MP4_API __declspec(dllexport)
#else
#define MW_MP4_API __declspec(dllimport)
#endif
#else
#define MW_MP4_API 
#endif

typedef struct _mw_mp4_handle_t{int32_t r;} *mw_mp4_handle_t;

typedef enum _mw_mp4_status
{
    MW_MP4_STATUS_SUCCESS = 0,
    MW_MP4_STATUS_UNEXPECTED_ERROR,
    MW_MP4_STATUS_INVALID_HANDLE,
    MW_MP4_STATUS_FILE_NAME_TOO_LONG,
    MW_MP4_STATUS_INVALID_PARAMETER,
    MW_MP4_STATUS_INVALID_CODEC_TYPE,
    MW_MP4_STATUS_INVALID_SUBTITLE_TYPE,
    MW_MP4_STATUS_INVALID_ADTS_STREAM,
    MW_MP4_STATUS_INVALID_VIDEO_STREAM,
    MW_MP4_STATUS_INVALID_VIDEO_TRACK,
    MW_MP4_STATUS_UNSUPPORTED,
    MW_MP4_STATUS_OPERATOR_NOT_PERMITTED,

    MW_MP4_STATUS_NO_SUCH_FILE_OR_DIR,
    MW_MP4_STATUS_PERMISSION_DENIED,
    MW_MP4_STATUS_DEVICE_OR_RESOURCE_BUSY,
    MW_MP4_STATUS_TOO_MANY_OPEN_FILES,
    MW_MP4_STATUS_NO_SPACE_LEFT,
    MW_MP4_STATUS_READONLY_FILE_SYSTEM,

    MW_MP4_STATUS_EXTERNAL_FUNC_FAILED,
    MW_MP4_STATUS_FILE_NOT_OPEN,
} mw_mp4_status_t;

typedef enum _mw_mp4_video_type {
    MW_MP4_VIDEO_TYPE_UNKNOWN = 0,
    MW_MP4_VIDEO_TYPE_H264    = 1,
    MW_MP4_VIDEO_TYPE_HEVC    = 2,
    MW_MP4_VIDEO_TYPE_H265    = MW_MP4_VIDEO_TYPE_HEVC
}mw_mp4_video_type_t;

typedef struct _mw_mp4_h264_parameter_set {
    uint8_t*		sps;        // can be nullptr if it's contained in the stream
    int16_t			sps_size;   // can be 0 if it's contained in the stream
    uint8_t*		pps;        // can be nullptr if it's contained in the stream
    int16_t			pps_size;   // can be 0 if it's contained in the stream
} mw_mp4_h264_parameter_set_t;

typedef struct _mw_mp4_hevc_parameter_set {
    uint8_t*		sps;            // can be nullptr if it's contained in the stream
    int16_t			sps_size;       // can be 0 if it's contained in the stream
    uint8_t*		pps;            // can be nullptr if it's contained in the stream
    int16_t			pps_size;       // can be 0 if it's contained in the stream
    uint8_t*		vps;            // can be nullptr if it's contained in the stream
    int16_t			vps_size;       // can be 0 if it's contained in the stream
} mw_mp4_hevc_parameter_set_t;

typedef struct _mw_mp4_video_info {
    mw_mp4_video_type_t codec_type;
    uint32_t		    timescale;
    uint16_t		    width;
    uint16_t		    height;

    union{
        mw_mp4_h264_parameter_set_t h264;
        mw_mp4_hevc_parameter_set_t hevc;
    };
} mw_mp4_video_info_t;

typedef enum _mw_mp4_audio_type {
    MW_MP4_AUDIO_TYPE_UNKNOWN    = 0,
    MW_MP4_AUDIO_TYPE_AAC        = 1,
    MW_MP4_AUDIO_TYPE_ADTS_AAC   = 2
}mw_mp4_audio_codec_t;

typedef struct _mw_mp4_audio_info {
    mw_mp4_audio_codec_t codec_type;
    uint32_t		     timescale;
    uint16_t		     sample_rate; // can be 0 if codec is aac with adts
    uint16_t		     channels; // can be 0 if codec is aac with  adts
    uint8_t			     profile; // can be 0 if codec is aac with  adts
} mw_mp4_audio_info_t;

typedef enum _mw_mp4_subtitle_type {
    MW_MP4_SUBTITLE_TYPE_UNKNOWN = 0,
    MW_MP4_SUBTITLE_TYPE_CC608   = 1,
    MW_MP4_SUBTITLE_TYPE_CC708   = 2
}mw_mp4_subtitle_type_t;

typedef struct _mw_mp4_subtitle_info {
    mw_mp4_subtitle_type_t  codec_type;
    uint32_t		        timescale;
} mw_mp4_subtitle_info_t;

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * @ingroup group_mp4_functions
 * create a handle to mux video/audio/subtitle stream to mp4 file
 * @param p_path the output file path
 * @return  If succeeded, it returns the mp4 handle; otherwise, it returns NULL.
 */
MW_MP4_API
mw_mp4_handle_t mw_mp4_open(const char * p_path);

/**
 * @ingroup group_mp4_functions
 * create a handle to mux video/audio/subtitle stream to mp4 file
 * @param p_path the output file path (wchar)
 * @return  If succeeded, it returns the mp4 handle; otherwise, it returns NULL.
 */

MW_MP4_API
mw_mp4_handle_t mw_mp4_open_ex(const wchar_t * p_path);

/**
* @ingroup group_mp4_functions
* set video track information, support codec H.264 and HEVC.
* @param handle mp4 handle.
* @param p_info video stream information.
* @return  return MW_MP4_STATUS_SUCCESS if success, else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_set_video(mw_mp4_handle_t handle, const mw_mp4_video_info_t* p_info);

/**
* @ingroup group_mp4_functions
* set audio stream information, support codec aac
* @param handle mp4 handle.
* @param p_info audio stream information.
* @return  return MW_MP4_STATUS_SUCCESS if success, else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_set_audio(mw_mp4_handle_t handle, const mw_mp4_audio_info_t* p_info);

/**
* @ingroup group_mp4_functions
* set subtitle(closed caption) stream information, support EIA-608 and EIA-708
* @param handle mp4 handle.
* @param p_info subtitle(closed caption) stream information.
* @return  return MW_MP4_STATUS_SUCCESS if success, else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_set_subtitle(mw_mp4_handle_t handle, const mw_mp4_subtitle_info_t* p_info);

/**
* @ingroup group_mp4_functions
* write a video frame to mp4 file.
* @param handle    mp4 handle.
* @param p_stream       video frame data
* @param size               video frame size
* @param timestamp       video frame timestamp
* @return  return MW_MP4_STATUS_SUCCESS if success, else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_write_video(mw_mp4_handle_t handle, const uint8_t * p_stream, uint32_t size, uint64_t timestamp);

/**
* @ingroup group_mp4_functions
* write an audio frame to mp4 file
* @param handle mp4 handle
* @param p_stream audio frame data
* @param size audio frame size
* @param timestamp audio frame timestamp
* @return  return MW_MP4_STATUS_SUCCESS if success, else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_write_audio(mw_mp4_handle_t handle, const uint8_t * p_stream, uint32_t size, uint64_t timestamp);

/**
* @ingroup group_mp4_functions
* write a subtitle(closed caption) frame to mp4 file
* @param handle mp4 handle
* @param p_stream subtitle frame data
* @param size subtitle frame size
* @param timestamp subtitle frame timestamp
* @return  return MW_MP4_STATUS_SUCCESS if success, else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_write_subtitle(mw_mp4_handle_t handle, const uint8_t * p_stream, uint32_t size, uint64_t timestamp);

/**
* @ingroup group_mp4_functions
* close an opened MP4 file handle
* @param handle mp4 file handle
* @return  return MW_MP4_STATUS_SUCCESS if success, else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_close(mw_mp4_handle_t handle);

/**
* @ingroup group_mp4_functions
* repair a broken file
* @param p_path the broken file path
* @param del automatic delete the redundancy file if repair succeeded.
* @return  return MW_MP4_STATUS_SUCCESS if success, else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_repair(const char * p_path, bool del);

/**
* @ingroup group_mp4_functions
* @brief repair a broken file
* @param path the broken file path(wchar_t)
* @param del automatic delete the redundancy file if repair succeeded.
* @return  return MW_STATUS_SUCCESS if successfully else error code
*/
MW_MP4_API
mw_mp4_status_t mw_mp4_repair_ex(const wchar_t * p_path, bool del);
#ifdef __cplusplus
}
#endif
#endif