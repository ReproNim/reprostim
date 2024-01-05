#ifndef MW_ERROR_CODE_H
#define MW_ERROR_CODE_H

/**
 * @ingroup group_cc_variables_enum
 * @brief MW_CC_RESULT
 * @details Closed Caption state code
 */
typedef enum _CC_RESULT{
    MW_CC_NO_ERROR,                         ///< Normal
    MW_CC_ERROR_ARGUMENT,                   ///< Error Parameter 
    MW_CC_OUT_OF_MEMORY,                    ///< Error memory storage 
    MW_CC_ANC_INVALID,                      ///< Invalid ANC is invalid
    MW_CC_ERROR_ANC_DID,                    ///< DID is not 0x61
    MW_CC_ERROR_ANC_SDID,                   ///< SDID is not 0x1 or 0x2
    MW_CC_ERROR_ANC_608_INVALID,            ///< Invalid 608ANC is invalid
    MW_CC_ERROR_ANC_608_LENGTH,             ///< Error length of 608ANC
    MW_CC_ERROR_ANC_708_INVALID,            ///< Invalid 708ANC
    MW_CC_ERROR_DECODER_NULL,               ///< 708 decoder is null
    MW_CC_ERROR_DECODE_DATA_NULL,           ///< Decoder is null
    MW_CC_ERROR_DECODE_DATA_SIZE,           ///< Error size of decoded data

    /*cc708_error*/
    MW_CC708_ERROR_ARGUMENT,                ///< Error 708 parameter
    MW_CC708_OUT_OF_MEMORY,                 ///< Error 708 storage memory
    MW_CC708_ERROR_TIME_CODE_NULL,          ///< Time code is null
    MW_CC708_ERROR_ANC_TIME_CODE_NULL,      ///< ANC time code is null
    MW_CC708_ERROR_ANC_TIME_CODE_LENGTH,    ///< Error Length of ANC time code 
    MW_CC708_ERROR_ANC_708_TIME_PACKET,     ///< Error ANC time code content
    MW_CC708_ERROR_ANC_708_DATA_SIZE,       ///< Error ANC data size
    MW_CC708_ERROR_ANC_708_DATA_PACKET,     ///< Error ANC packet 
    MW_CC708_ERROR_ANC_708_SINFO_PACKET,    ///< Error ANC segment info 

    /*cc608_error*/
    MW_CC608_ERROR_ARGUMENT,                ///< Error 608 parameter
    MW_CC608_OUT_OF_MEMORY,                 ///< Error 608 memory storage 
    MW_CC608_ERROR_FIELD,                   ///< Error 608 field

    /*cc render*/
    MW_CC_RENDER_ERROR_ARGUMENT,			///< Error render parameter
    MW_CC_RENDER_SIZE_ERROR,				///< Error render size
    MW_CC_RENDER_FONT_ERROR,				///< Error uploaded font
    MW_CC_RENDER_CC708_WINDOW_NUM_ERROR,	///< Error number of windows
}MW_CC_RESULT;

#endif // MW_ERROR_CODE_H
