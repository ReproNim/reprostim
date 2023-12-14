#ifndef MW_ERROR_CODE_H
#define MW_ERROR_CODE_H

typedef enum _CC_RESULT{
    /*cc_error*/
    MW_CC_NO_ERROR,                         //no error
    MW_CC_ERROR_ARGUMENT,                   //argument error
    MW_CC_OUT_OF_MEMORY,                    //out of memory
    MW_CC_ANC_INVALID,                      //anc packet invalid
    MW_CC_ERROR_ANC_DID,                    //DID is not 0x61
    MW_CC_ERROR_ANC_SDID,                   //SDID is not 0x1 or 0x2
    MW_CC_ERROR_ANC_608_INVALID,            //608 anc packet invalid
    MW_CC_ERROR_ANC_608_LENGTH,             //608 anc packet length error
    MW_CC_ERROR_ANC_708_INVALID,            //708 anc packet invalid
    MW_CC_ERROR_DECODER_NULL,               //708 decoder pointer is null
    MW_CC_ERROR_DECODE_DATA_NULL,           //decode data pointer is null
    MW_CC_ERROR_DECODE_DATA_SIZE,           //decode data szie wrong

    /*cc708_error*/
    MW_CC708_ERROR_ARGUMENT,                //708 argument error
    MW_CC708_OUT_OF_MEMORY,                 //708 out of memory
    MW_CC708_ERROR_TIME_CODE_NULL,          //time code pointer is null
    MW_CC708_ERROR_ANC_TIME_CODE_NULL,      //anc time code pointer is null
    MW_CC708_ERROR_ANC_TIME_CODE_LENGTH,    //time code lenth wrong
    MW_CC708_ERROR_ANC_708_TIME_PACKET,     //anc packet time code context wrong
    MW_CC708_ERROR_ANC_708_DATA_SIZE,       //anc packet data segment's size wrong
    MW_CC708_ERROR_ANC_708_DATA_PACKET,     //anc packet data segment context wrong
    MW_CC708_ERROR_ANC_708_SINFO_PACKET,    //anc packet service info segment context wrong

    /*cc608_error*/
    MW_CC608_ERROR_ARGUMENT,                //608 atgument error
    MW_CC608_OUT_OF_MEMORY,                 //608 out of memory
    MW_CC608_ERROR_FIELD,                   //608 field wrong

    /*cc render*/
    MW_CC_RENDER_ERROR_ARGUMENT,			//argument
    MW_CC_RENDER_SIZE_ERROR,				//size error
    MW_CC_RENDER_FONT_ERROR,				//load font failed
    MW_CC_RENDER_CC708_WINDOW_NUM_ERROR,	//window num error
}MW_CC_RESULT;

#endif // MW_ERROR_CODE_H
