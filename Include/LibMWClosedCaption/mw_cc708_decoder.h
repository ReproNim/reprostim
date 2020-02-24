#ifndef MWCCDECODER_H
#define MWCCDECODER_H

////////////////////////////////////////////////////////////////////////////////
// Copyright (c) 2011-2018 Magewell Electronics Co., Ltd. (Nanjing)
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
 * @brief MWCreateCC708Decoder
 *        Creates the 708 decoder
 * @return Returns NULL if failed,otherwise return the pointer
 */
LIBMWCCDECODER_API 
mw_cc708_decoder_t *MWCreateCC708Decoder();

/**
 * @brief MWDestoryCC708Decoder
 *        Destorys the 708 decoder
 * @param[in] pDecoder  The pointer of the decoder
 */
LIBMWCCDECODER_API 
void MWDestoryCC708Decoder(mw_cc708_decoder_t *pDecoder);

/**
 * @brief MWResetCC708Decoder
 *        Resets the 708 decoder
 * @param[in] pDecoder  The pointer of the decoder
 */
LIBMWCCDECODER_API
void MWResetCC708Decoder(mw_cc708_decoder_t *pDecoder);

/**
 * @brief MWSetCC708DecoderCallback
 *        Sets the callbalck of the decoder to remind the output update
 * @param[in] pDecoder  The pointer of the decoder
 * @param[in] pHandle   The pointer of the callback function
 * @param[in] pUserdata The pointer of the callback caller
 */
LIBMWCCDECODER_API 
void MWSetCC708DecoderCallback(mw_cc708_decoder_t *pDecoder, void(*pHandle)(int service, void *userdata), void *pUserdata);

/**
 * @brief MWSetCC708DecodeType
 *        Sets decode 608 data or 708 data of the input data
 * @param[in] pDecoder  The pointer of the decoder
 * @param[in] b608      If true,it will decode 608 data of the input data
 * @param[in] b708      If true,it will decode 708 data of the input data
 */
LIBMWCCDECODER_API
void MWSetCC708DecodeType(mw_cc708_decoder_t *pDecoder, bool b608, bool b708);

/**
 * @brief MWEnableOutputChannel
 *        Enable output channel
 * @param[in] pDecoder  The pointer of the decoder
 * @param[in] mcc       The symbol of channel
 * @return Returns MW_CC_NO_ERROR when all is right
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWEnableOutputChannel(mw_cc708_decoder_t *pDecoder, mw_cc708_channel_t mcc);

/**
 * @brief MWEnableOutputChannels
 * @param[in] pDecoder  The pointer of the decoder
 * @param[in] mcc       The pointer to channel arrays
 * @param[in] array_num The length of channel arrays
 * @return Returns MW_CC_NO_ERROR when all is right
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWEnableOutputChannels(mw_cc708_decoder_t *pDecoder, mw_cc708_channel_t *mcc, int array_num);

/**
 * @brief MWDisableOutputChannel
 *        Disable output channel
 * @param[in] pDecoder  The pointer of the decoder
 * @param[in] mcc       The symbol of channel
 * @return Returns MW_CC_NO_ERROR when all is right
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWDisableOutputChannel(mw_cc708_decoder_t *pDecoder, mw_cc708_channel_t mcc);

/**
 * @brief MWDisableOutputChannels
 *        Disable output channel
 * @param[in] pDecoder  The pointer of the decoder
 * @param[in] mcc       The pointer to channel arrays
 * @param[in] array_num The length of channel arrays
 * @return Returns MW_CC_NO_ERROR when all is right
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWDisableOutputChannels(mw_cc708_decoder_t *pDecoder, mw_cc708_channel_t *mcc,int array_num);

/**
 * @brief MWDecodeCC608
 *        Decodes CC608 ANC data
 * @param[in] pDecoder      The pointer of the decoder
 * @param[in] pData         The pointer of anc data
 * @param[in] nDatalength   Length of anc data
 * @return Returns MW_CC_NO_ERROR when all is right
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWDecodeCC608(mw_cc708_decoder_t *pDecoder, const unsigned char *pData, int nDatalength);

/**
 * @brief MWDecodeCC708
 *        Decodes CC708 ANC data
 * @param[in] pDecoder      The pointer of the decoder
 * @param[in] pData         The pointer of anc data
 * @param[in] nDatalength   Length of anc data
 * @return Returns MW_CC_NO_ERROR when all is right
 */
LIBMWCCDECODER_API
MW_CC_RESULT MWDecodeCC708(mw_cc708_decoder_t *pDecoder, const unsigned char *pData, int nDatalength);

#ifdef __cplusplus
}
#endif
#endif