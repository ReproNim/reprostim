#ifndef MW708BASE_H
#define MW708BASE_H
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

#include <stdint.h>
#if (defined __linux__)
#include <stddef.h>
#endif

#define CC608_ROWS     15
#define CC608_COLUMNS  32
#define CC608_CHANNELS 4

typedef struct _cc708_decoder mw_cc708_decoder_t;
typedef struct _cc708_service_all_decoders mw_cc708_service_all_decoders_t;

/**
  * cc608 background color
*/
typedef enum _cc608_background_color
{
    MW_BAC_WHITE,                       //rgba(255,255,255,255)
    MW_BAC_WHITE_SEMI,                  //rgba(255,255,255,122)
    MW_BAC_GREEN,                       //rgba(0,255,0,255)
    MW_BAC_GREEN_SEMI,                  //rgba(0,255,0,122)
    MW_BAC_BLUE,                        //rgba(0,0,255,255)
    MW_BAC_BLUE_SEMI,                   //rgba(0,0,255,122)
    MW_BAC_CYAN,                        //rgba(0,255,255,255)
    MW_BAC_CYAN_SEMI,                   //rgba(0,255,255,122)
    MW_BAC_RED,                         //rgba(255,0,0,255)
    MW_BAC_RED_SEMI,                    //rgba(255,0,0,122)
    MW_BAC_YELLOW,                      //rgba(255,255,0,255)
    MW_BAC_YELLOW_SEMI,                 //rgba(255,255,0,122)
    MW_BAC_MAGENTA,                     //rgba(255,0,255,255)
    MW_BAC_MAGENTA_SEMI,                //rgba(255,0,255,122)
    MW_BAC_BLACK,                       //rgba(0,0,0,255)
    MW_BAC_BLACK_SEMI,                  //rgba(0,0,0,122)
    MW_BAC_TRANSPARENT,                 //rgba(0,0,0,0)
    MW_FAC_BLACK,                       //font color
    MW_FAC_BLACK_UNDERLINE              //font color
}mw_cc608_background_color_t;

/**
  * cc608 font color
 */
typedef enum _cc608_foreground_color
{
    MW_FG_WHITE = 0,
    MW_FG_GREEN,
    MW_FG_BLUE,
    MW_FG_CYAN,
    MW_FG_RED,
    MW_FG_YELLOW,
    MW_FG_MAGENTA,
    MW_FG_USERDEFINED,
    MW_FG_BLACK,
    MW_FG_TRANSPARENT
} mw_cc608_foreground_color_t;

/**
  * cc708 channel -1 - -4 608
  *               -5      608_all
  *                1 - 63 708
  *                64     708_all
  *                0      all
*/
typedef enum _cc708_channel{
    MW_CC608_CC1=-1,
    MW_CC608_CC2=-2,
    MW_CC608_CC3=-3,
    MW_CC608_CC4=-4,
    MW_CC608_ALL=-5,

    MW_CC_ALL=0,

    MW_CC708_SERVICE01=1,
    MW_CC708_SERVICE02,
    MW_CC708_SERVICE03,
    MW_CC708_SERVICE04,
    MW_CC708_SERVICE05,
    MW_CC708_SERVICE06,
    MW_CC708_SERVICE07,
    MW_CC708_SERVICE08,
    MW_CC708_SERVICE09,

    MW_CC708_SERVICE10,
    MW_CC708_SERVICE11,
    MW_CC708_SERVICE12,
    MW_CC708_SERVICE13,
    MW_CC708_SERVICE14,
    MW_CC708_SERVICE15,
    MW_CC708_SERVICE16,
    MW_CC708_SERVICE17,
    MW_CC708_SERVICE18,
    MW_CC708_SERVICE19,

    MW_CC708_SERVICE20,
    MW_CC708_SERVICE21,
    MW_CC708_SERVICE22,
    MW_CC708_SERVICE23,
    MW_CC708_SERVICE24,
    MW_CC708_SERVICE25,
    MW_CC708_SERVICE26,
    MW_CC708_SERVICE27,
    MW_CC708_SERVICE28,
    MW_CC708_SERVICE29,

    MW_CC708_SERVICE30,
    MW_CC708_SERVICE31,
    MW_CC708_SERVICE32,
    MW_CC708_SERVICE33,
    MW_CC708_SERVICE34,
    MW_CC708_SERVICE35,
    MW_CC708_SERVICE36,
    MW_CC708_SERVICE37,
    MW_CC708_SERVICE38,
    MW_CC708_SERVICE39,

    MW_CC708_SERVICE40,
    MW_CC708_SERVICE41,
    MW_CC708_SERVICE42,
    MW_CC708_SERVICE43,
    MW_CC708_SERVICE44,
    MW_CC708_SERVICE45,
    MW_CC708_SERVICE46,
    MW_CC708_SERVICE47,
    MW_CC708_SERVICE48,
    MW_CC708_SERVICE49,

    MW_CC708_SERVICE50,
    MW_CC708_SERVICE51,
    MW_CC708_SERVICE52,
    MW_CC708_SERVICE53,
    MW_CC708_SERVICE54,
    MW_CC708_SERVICE55,
    MW_CC708_SERVICE56,
    MW_CC708_SERVICE57,
    MW_CC708_SERVICE58,
    MW_CC708_SERVICE59,

    MW_CC708_SERVICE60,
    MW_CC708_SERVICE61,
    MW_CC708_SERVICE62,
    MW_CC708_SERVICE63,

    MW_CC708_ALL=64,
}mw_cc708_channel_t;

/**
  *font attribute
*/
typedef struct _cc608_attributes
{
    unsigned char italic;                              //0 false 1 true
    unsigned char underline;                           //0 false 1 true
    mw_cc608_foreground_color_t foreground;            //MW_FG_
    mw_cc608_background_color_t background;            //MW_BAC_
}mw_cc608_attributes_t;

/**
  *character cell
*/
typedef struct _cc608_char_cell
{
    uint32_t ch;                                        //charceter unicode
    mw_cc608_attributes_t attributes;                   //color and font
    int inited;                                         //1 ch valid,0 ch invalid
}mw_cc608_char_cell_t;

/**
  *a single row in the closed captioning memory
*/
typedef struct _cc608_row
{
    mw_cc608_char_cell_t cells[CC608_COLUMNS];          //character row
    int16_t pos;                                        //cursor pos
    int16_t num_chars;                                  //number of characters
    mw_cc608_attributes_t pac_attr;                     //current color and fomt
}mw_cc608_row_t;

/**
closed caption for a single channel
*/
typedef struct _cc608_buffer
{
    mw_cc608_row_t rows[CC608_ROWS];                    //character columns
    int16_t rowpos;                                     //cursor pos row
    mw_cc608_attributes_t pac_attr;                     //current attribute

    int64_t start_time;                                 //strat time of this buffer
    int64_t end_time;                                   //end time of this buffer

    mw_cc708_channel_t channel;                         //channel id

    char *xds_str;                                      //xds string
    int16_t xds_len;                                     //length of xds string
    int cur_xds_packet_class;                           //class of xds string
}mw_cc608_buffer_t;

/**
  * captioning memory for all channels
*/
typedef struct _cc608_memory
{
    mw_cc608_buffer_t channel[CC608_CHANNELS];          //channel screen buffer
    int channel_no;                                     //currently selected channel
}mw_cc608_memory_t;

/**
  * cc608 caption show style
*/
typedef enum _cc608_style
{
    MW_CC608_ROLLUP     = 1,                            //roll up show style
    MW_CC608_PAINTON,                                   //paint on show style
    MW_CC608_POPON,                                     //pop on show style
    MW_CC608_TEXT,                                      //text show style
}mw_cc608_style_t;

/**
  * record of active cc608 channels
  * cc1-cc4
*/
typedef struct _cc608_active_channel{
    int16_t m_active_channels[CC608_CHANNELS];          //record of active channels
}mw_cc608_active_channel_t;

/**
  *The closed captioning decoder data structure
*/
typedef struct _cc608_decoder
{
    mw_cc608_memory_t buffer[2];                        //on_buffer and off_buffer
    mw_cc608_memory_t *on_buf;                          //pointer of show buffer
    mw_cc608_memory_t *off_buf;                         //pointer of back screen
    mw_cc608_memory_t **active;                         //pointer of pointer of active buffer

    mw_cc608_active_channel_t m_activeChannels;         //record of active channel,1 means active

    uint32_t lastcode;                                  //recoord of lastcode

    uint16_t rollup_rows;                               //rollup rows
    mw_cc608_style_t style;                             //paint style

    void *userdata;                                     //pointer of callback object
    void(*callback)(int service, void *userdata);       //pointer of callback;

    mw_cc708_decoder_t *parent;                         //pointer of MW_CC708_Decoder
    void(*cc708decodercallback)(mw_cc708_decoder_t *parent, bool t_b608, int t_nService);//pointer of MW_CC708_decoder

    char text[CC608_ROWS*CC608_COLUMNS + 1];            //may delete
    int textlen;                                        //maydelete
}mw_cc608_decoder_t;

/**
  *base setting of 708 cc
*/
#define MAX_708_PACKET_LENGTH           128
#define CCX_DECODERS_708_MAX_SERVICES   63
#define I708_MAX_ROWS                   15
#define I708_MAX_COLUMNS                42

/**
* This value should be 32, but there were 16-bit encoded samples (from Korea),
* where RowCount calculated another way and equals 46 (23[8bit]*2)
*/
#define I708_MAX_COLUMNS_2				32
#define I708_SCREENGRID_ROWS            75
#define I708_SCREENGRID_COLUMNS         210
#define I708_MAX_WINDOWS                8

/**
time_code_section_id    8 uimsbf 0x71
Reserved                2 '11'
tc_10hrs                2 uimsbf Tens of hours
tc_1hrs                 4 uimsbf Units of hours
Reserved                1 '1'
tc_10min                3 uimsbf Tens of minutes
tc_1min                 4 uimsbf Units of minutes
tc_field_flag           1 uimsbf see text
tc_10sec                3 uimsbf Tens of seconds
tc_1sec                 4 uimsbf Units of seconds
Reserved                1 '1'
drop_frame_flag         1 uimsbf Drop frame flag
tc_10fr                 3 uimsbf Tens of frames
tc_1fr                  4 uimsbf Units of frames
*/
typedef struct _cea708_time_code//0x71
{
	unsigned char m_csTimeCode[4];
    int16_t n10hour;
    int16_t n1hour;
    int16_t n10min;
    int16_t n1min;
    int16_t n10sec;
    int16_t n1sec;
    int16_t n10fra;
    int16_t n1fra;
    bool bdropfra;                      //wether drop frame
}mw_cea708_time_code_t;

/**
window justify
*/
typedef enum _cea708_windows_attrib_justify
{
    MW_CC708_WA_LEFT = 0,
    MW_CC708_WA_RIGHT,
    MW_CC708_WA_CENTER,
    MW_CC708_WA_FULL,
}mw_cea708_windows_attrib_justify_t;

/**
window print direction
*/
typedef enum _cea708_windows_attrib_print_direction
{
    MW_CC708_PD_LEFT_TO_RIGHT = 0,
    MW_CC708_PD_RIGHT_TO_LEFT,
    MW_CC708_PD_TOP_TO_BOTTOM,
    MW_CC708_PD_BOTTOM_TO_TOP,
}mw_cea708_windows_attrib_print_direction_t;

/**
window scroll direction
*/
typedef enum _cea708_windows_attrib_scroll_direction
{
    MW_CC708_SD_LEFT_TO_RIGHT = 0,
    MW_CC708_SD_RIGHT_TO_LEFT,
    MW_CC708_SD_TOP_TO_BOTTOM,
    MW_CC708_SD_BOTTOM_TO_TOP,
}mw_cea708_windows_attrib_scroll_direction_t;

/**
window scroll display effect
*/
typedef enum _cea708_windows_attrib_scroll_display_effect
{
    MW_CC708_SDE_SNAP = 0,
    MW_CC708_SDE_FADE,
    MW_CC708_SDE_WIPE,
}mw_cea708_windows_attrib_scroll_display_effect_t;

/**
window effect direction
*/
typedef enum _cea708_windows_attrib_effect_direction
{
    MW_CC708_ED_LEFT_TO_RIGHT = 0,
    MW_CC708_ED_RIGHT_TO_LEFT,
    MW_CC708_ED_TOP_TO_BOTTOM,
    MW_CC708_ED_BOTTOM_TO_TOP,
}mw_cea708_windows_attrib_effect_direction_t;

/**
window fill opacity
*/
typedef enum _cea708_windows_attrib_fill_opacity
{
    MW_CC708_FO_SOLID = 0,
    MW_CC708_FO_FLASH,
    MW_CC708_FO_TRANSLUENT,
    MW_CC708_FO_TRANSPARENT,
}mw_cea708_windows_attrib_fill_opacity_t;

/**
window border type
*/
typedef enum _cea708_windows_attrib_border_type
{
    MW_CC708_BT_NONE = 0,
    MW_CC708_BT_RAISED,
    MW_CC708_BT_DEPRESSED,
    MW_CC708_BT_UNIFORM,
    MW_CC708_BT_SHADOW_LEFT,
    MW_CC708_BT_SHADOW_RIGHT,
}mw_cea708_windows_attrib_border_type_t;

/**
pen size:mainly for character
*/
typedef enum _cea_pen_attrib_size
{
    MW_CC708_PENSIZE_SMALL = 0,
    MW_CC708_PENSIZE_STANDARD,
    MW_CC708_PENSIZE_LARGE,
}mw_cea_pen_attrib_size_t;

/**
font style
*/
typedef enum _cea708_pen_attrib_font_style
{
    MW_CC708_FS_DEFAULT_OR_DEFINED=0,
    MW_CC708_FS_MONOSPACED_WITH_SERIFS,
    MW_CC708_FS_PROPORTIONALLY_SPACED_WITH_SERIFS,
    MW_CC708_FS_MONOSPACED_WITHOUT_SERIFS,
    MW_CC708_FS_PROPORTIONALLY_SPACED_WITHOUT_SERIFS,
    MW_CC708_FS_CAUSAL_FONT_TYPE,
    MW_CC708_FS_CURISVE_FONT_TYPE,
    MW_CC708_FS_SMALL_CAPTIALS,
}mw_cea708_pen_attrib_font_style_t;

/**
text tag
*/
typedef enum _cea708_pen_attrib_texttag
{
    MW_CC708_PTEXTTAG_DIALOG = 0,
    MW_CC708_PTEXTTAG_SOURCE_OR_SPEAKER_ID,
    MW_CC708_PTEXTTAG_ELECTRONIC_VOICE,
    MW_CC708_PTEXTTAG_FOREIGN_LAUNGUANGE,
    MW_CC708_PTEXTTAG_VOICEOVER,
    MW_CC708_PTEXTTAG_AUDIBLE_TRANSLATION,
    MW_CC708_PTEXTTAG_SUBTITLE_TRANSLATION,
    MW_CC708_PTEXTTAG_VOICE_QUALITY_DESCRIPTION,
    MW_CC708_PTEXTTAG_SONG_LYRICS,
    MW_CC708_PTEXTTAG_SOUND_EFFECT_DESCRIPTION,
    MW_CC708_PTEXTTAG_MUSICAL_SCORE_DESCRIPTION,
    MW_CC708_PTEXTTAG_EXPLETIVE,
    MW_CC708_PTEXTTAG_UNDEFINED_12,
    MW_CC708_PTEXTTAG_UNDEFINED_13,
    MW_CC708_PTEXTTAG_UNDEFINED_14,
    MW_CC708_PTEXTTAG_NOT_TO_BE_DISPLAYED,
}mw_cea708_pen_attrib_texttag_t;

/**
pen offset
*/
typedef enum _cea_pen_attrib_offset
{
    MW_CC708_POF_SUBSCRIPT=0,
    MW_CC708_POF_NORMAL,
    MW_CC708_POF_SUPERSCRIPT,
}mw_cea_pen_attrib_offset_t;

/**
pen edge type
*/
typedef enum _cea_pen_attrib_edgetype
{
    MW_CC708_PET_NONE = 0,
    MW_CC708_PET_RAISED,
    MW_CC708_PET_DEPRESSED,
    MW_CC708_PET_UNIFORM,
    MW_CC708_PET_LEFT_DROP_SHADOW,
    MW_CC708_PET_RIGHT_DROP_SHADOW,
}mw_cea_pen_attrib_edgetype_t;

/**
window anchor point
*/
typedef enum _cea_anchor_points
{
    MW_CC708_ANCHORPOINT_TOP_LEFT = 0,
    MW_CC708_ANCHORPOINT_TOP_CENTER,
    MW_CC708_ANCHORPOINT_TOP_RIGHT,
    MW_CC708_ANCHORPOINT_MIDDLE_LEFT,
    MW_CC708_ANCHORPOINT_MIDDLE_CENTER,
    MW_CC708_ANCHORPOINT_MIDDLE_RIGHT,
    MW_CC708_ANCHORPOINT_BOTTOM_LEFT,
    MW_CC708_ANCHORPOINT_BOTTOM_CENTER,
    MW_CC708_ANCHORPOINT_BOTTOM_RIGHT,
}mw_cea_anchor_points_t;

typedef struct _cc708_cell
{
    uint16_t sym;                   //symbol itself, unicode 16 bits
    uint16_t init;                  //initialized or not. could be 0 or 1
} mw_cc708_cell_t;

#define MW_708CELL_SYM_SET(x, c) {x.init = 1; x.sym = c;}
#define MW_708CELL_SYM_SET_16(x, c1, c2) {x.init = 1; x.sym = (c1 << 8) | c2;}
#define MW_708CELL_SYM(x) ((unsigned char)(x.sym))
#define MW_708CELL_SYM_IS_EMPTY(x) (x.init == 0)
#define MW_708CELL_SYM_IS_SET(x) (x.init == 1)
#define MW_708CELL_MUSICAL_NOTE_CHAR 9836	// Unicode Character 'BEAMED SIXTEENTH NOTES'

/**
708 pen color
*/
typedef struct _cc708_pen_color  //adjust
{
    int16_t fg_color;           //foreground_color & 0x3f 2 bit r,2 bit g,2 bit a
    mw_cea708_windows_attrib_fill_opacity_t fg_opacity;
    int16_t bg_color;           //background_color & 0x3f 2 bit r,2 bit g,2 bit a
    mw_cea708_windows_attrib_fill_opacity_t bg_opacity;
    int16_t edge_color;         //edge_color & 0x3f 2 bit r,2 bit g,2 bit a
}mw_cc708_pen_color_t;

/**
708 pen attribue
*/
typedef struct _cc708_pen_attrib //adjust
{
    mw_cea_pen_attrib_size_t pen_size;
    mw_cea_pen_attrib_offset_t offset;
    mw_cea708_pen_attrib_texttag_t text_tag;
    mw_cea708_pen_attrib_font_style_t font_tag;
    mw_cea_pen_attrib_edgetype_t edge_type;
    int16_t underline;                          //1 underline
    int16_t italic;                             //1 italic
}mw_cc708_pen_attrib_t;

/**
708 window attribute
*/
typedef struct _cc708_window_attrib
{
    mw_cea708_windows_attrib_justify_t justify;
    mw_cea708_windows_attrib_print_direction_t print_dir;
    mw_cea708_windows_attrib_scroll_direction_t scroll_dir;
    int16_t word_wrap;                                          //0 1
    mw_cea708_windows_attrib_scroll_display_effect_t display_eff;
    mw_cea708_windows_attrib_effect_direction_t effect_dir;
    int16_t effect_speed;                                       //1-15 (x*0.5 seconds)
    int16_t fill_color;                                         //fill_color & 0x3f 2 bit r,2 bit g,2 bit a
    mw_cea708_windows_attrib_fill_opacity_t fill_opacity;
    mw_cea708_windows_attrib_border_type_t border_type;
    int16_t border_color;                                       //bord_color & 0x3f 2 bit r,2 bit g,2 bit a
    int16_t border_type01;                                      //using to cal bordtype
}mw_cc708_window_attrib_t;

/**
708 window
*/
typedef struct _cc708_window
{
    int16_t is_defined;                         //1 means defined
    int16_t number;                             //window index
    int16_t priority;                           //priority
    int16_t col_lock;                           //1 means locked
    int16_t row_lock;                           //1 means locked
    int16_t visible;                            //1 means visible
    int16_t anchor_vertical;                    //vertical pos
    int16_t relative_pos;                       //1 means relative,o means absolute
    int16_t anchor_horizontal;                  //horizontal pos
    int16_t row_count;                          //row count
    mw_cea_anchor_points_t anchor_point;        //anchor point
    int16_t col_count;                          //column count
    int16_t pen_style;                          //pen style index
    int16_t win_style;                          //win style index
    unsigned char commands[6];                  //commands used to avoid repeat
    mw_cc708_window_attrib_t window_attrib;
    mw_cc708_pen_attrib_t pen_attric;
    mw_cc708_pen_color_t pen_color;
    int16_t pen_row;
    int16_t pen_coloumn;

    mw_cc708_cell_t *cell_rows[I708_MAX_ROWS];
    mw_cc708_pen_color_t pen_colors[I708_MAX_ROWS][I708_SCREENGRID_COLUMNS];
    mw_cc708_pen_attrib_t pen_attribs[I708_MAX_ROWS][I708_SCREENGRID_COLUMNS];
    int16_t memory_reserved;                    //memory is malloc 1,free 0
    int16_t is_empty;                           //has content 0 else 1
}mw_cc708_window_t;

typedef struct _cc708_tv_window_screen{
    mw_cc708_window_t windows[I708_MAX_WINDOWS];
    int16_t nwindow_num;
}mw_cc708_tv_window_screen_t;


/**
708 service decoder
*/
typedef struct _cc708_service_decoder
{
    mw_cc708_window_t windows[I708_MAX_WINDOWS];
    int16_t current_window;
    int16_t inited;
    int16_t service;                //service_number 0-62

    mw_cc708_tv_window_screen_t m_win_screen;

    void *userdata;
    void(*callback)(int service, void *userdata);
    mw_cc708_decoder_t *parent;
    void(*cc708decodercallback)(mw_cc708_decoder_t *parent, bool t_b608, int t_nService);

    mw_cc708_service_all_decoders_t *m_pSADParent;
}mw_cc708_service_decoder_t;

struct _cc708_service_all_decoders
{
    mw_cc708_service_decoder_t **cc708_service_decoder;
    int16_t  nactive_service_count;                           //service active count
    int16_t  nis_active;                                      //active id
    int16_t  service_active[CCX_DECODERS_708_MAX_SERVICES];   //record of active
    mw_cc708_decoder_t *parent;
};

struct _cc708_decoder
{
    bool binited;

    mw_cc708_service_all_decoders_t *cc708_sad_decoders;
    mw_cc608_decoder_t *cc608_decoder;

    unsigned char current_packet[MAX_708_PACKET_LENGTH];
    int16_t ncurrent_packet_length;
    int16_t nlast_seq;

    bool btrans_cc708;                                      //default true (if false 708 will not trans)
    bool btrans_cc608;                                      //default true (if false 608 will not trans)
    mw_cc608_buffer_t cc608_buffer;

    mw_cc708_tv_window_screen_t cc708_window_screen;


    bool bshow_cc708;                                       //true show 708
    bool bshow_cc608;                                       //true show 608

    bool bhas_cc708;                                        //true means input has 608
    bool bhas_cc608;                                        //true means input has 708

    bool bcc608_output[4];                                  //0-3 true means show
    bool bcc708_output[63];                                 //0-62 true means show

	void *userdata;
	void(*callback)(int service, void *userdata);

	int nlast_cdp_counter;
	int ncurrent_cdp_counter;
};

#endif
