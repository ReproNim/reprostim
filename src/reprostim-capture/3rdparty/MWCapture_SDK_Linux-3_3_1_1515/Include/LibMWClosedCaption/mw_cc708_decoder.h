#ifndef MWCCDECODER_H
#define MWCCDECODER_H

////////////////////////////////////////////////////////////////////////////////
// Copyright (c) 2011-2019 Magewell Electronics Co., Ltd. (Nanjing)
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the "Software"),
// to deal in the Software without restriction, including without limitation
// the rights to use, copy, modify, merge, publish, distribute, sublicense,
// and/or sell copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
////////////////////////////////////////////////////////////////////////////////

#pragma once

#ifdef LIBMWCCDECODER_EXPORTS
#define LIBMWCCDECODER_API __declspec(dllexport)
#elif LIBMWCCDECODER_DLL
#define LIBMWCCDECODER_API __declspec(dllimport)
#else
#define LIBMWCCDECODER_API
#endif

#include "mw_cc708_base_types.h"
#include "mw_error_code.h"

#ifdef __cplusplus

extern "C"
{
#endif

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWCreateCC708Decoder
 *        Creats CC708 decoder
 * @return If the function call succeeds, the CC708 decoder handle is returned; otherwise, the null value is returned.
 */
LIBMWCCDECODER_API 
mw_cc708_decoder_t *MWCreateCC708Decoder();

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWDestoryCC708Decoder
 *        Unregisters CC708 decoder
 * @param[in] pDecoder  Decoder pointer
 */
LIBMWCCDECODER_API 
void MWDestoryCC708Decoder(mw_cc708_decoder_t *pDecoder);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWResetCC708Decoder
 *        Resets CC708 decoder
 * @param[in] pDecoder  CC708 decoder
 */
LIBMWCCDECODER_API
void MWResetCC708Decoder(mw_cc708_decoder_t *pDecoder);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWSetCC708DecoderCallback
 *        Sets CC708 decoder callback function
 * @param[in] pDecoder  CC708 decoder
 * @param[in] pHandle   Callback functions
 * @param[in] pUserdata Callback object
 */
LIBMWCCDECODER_API 
void MWSetCC708DecoderCallback(mw_cc708_decoder_t *pDecoder, void(*pHandle)(int service, void *userdata), void *pUserdata);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWSetCC708DecodeType
 *        Sets CC708 decoder to parsing CC data types
 * @param[in] pDecoder  CC708 decoder
 * @param[in] b608      Whether to decode cc608
 * @param[in] b708      Whether to decode cc708
 */
LIBMWCCDECODER_API
void MWSetCC708DecodeType(mw_cc708_decoder_t *pDecoder, bool b608, bool b708);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWEnableOutputChannel
 *        Sets the decoded CC output channel 
 * @param[in] pDecoder  CC708 decoder
 * @param[in] mcc       Output channel
 * @return Returns #MW_CC_NO_ERROR 
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWEnableOutputChannel(mw_cc708_decoder_t *pDecoder, mw_cc708_channel_t mcc);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWEnableOutputChannels
 *        Sets the decoded CC output channels 
 * @param[in] pDecoder  CC708 decoder
 * @param[in] mcc       Output channel array
 * @param[in] array_num Length of output channel array
 * @return Returns #MW_CC_NO_ERROR 
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWEnableOutputChannels(mw_cc708_decoder_t *pDecoder, mw_cc708_channel_t *mcc, int array_num);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWDisableOutputChannel
 *        Sets the channels not to output CC
 * @param[in] pDecoder  CC708 decoder
 * @param[in] mcc       Output channels 
 * @return Returns #MW_CC_NO_ERROR 
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWDisableOutputChannel(mw_cc708_decoder_t *pDecoder, mw_cc708_channel_t mcc);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWDisableOutputChannels
 *        Length of output channel array
 * @param[in] pDecoder  CC708 decoder
 * @param[in] mcc       Output channel array
 * @param[in] array_num Length of output channel array
 * @return Returns #MW_CC_NO_ERROR 
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWDisableOutputChannels(mw_cc708_decoder_t *pDecoder, mw_cc708_channel_t *mcc,int array_num);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWDecodeCC608
 *        Decodes cc608 ANC
 * @param[in] pDecoder      CC708 decoder
 * @param[in] pData         ANC
 * @param[in] nDatalength   Length of ANC
 * @return Returns #MW_CC_NO_ERROR 
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWDecodeCC608(mw_cc708_decoder_t *pDecoder, const unsigned char *pData, int nDatalength);

/**
 * @ingroup group_cc_functions_decoder
 * @brief MWDecodeCC708
 *        Decodes cc708 ANC
 * @param[in] pDecoder      CC708 decoder
 * @param[in] pData         ANC
 * @param[in] nDatalength   Length of ANC
 * @return Returns #MW_CC_NO_ERROR 
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWDecodeCC708(mw_cc708_decoder_t *pDecoder, const unsigned char *pData, int nDatalength);

#ifdef __cplusplus
}
#endif
#endif