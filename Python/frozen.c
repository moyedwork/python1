
/* Frozen modules initializer
 *
 * Frozen modules are written to header files by Programs/_freeze_module.
 * These files are typically put in Python/frozen_modules/.  Each holds
 * an array of bytes named "_Py_M__<module>", which is used below.
 *
 * These files must be regenerated any time the corresponding .pyc
 * file would change (including with changes to the compiler, bytecode
 * format, marshal format).  This can be done with "make regen-frozen".
 * That make target just runs Tools/scripts/freeze_modules.py.
 *
 * The freeze_modules.py script also determines which modules get
 * frozen.  Update the list at the top of the script to add, remove,
 * or modify the target modules.  Then run the script
 * (or run "make regen-frozen").
 *
 * The script does the following:
 *
 * 1. run Programs/_freeze_module on the target modules
 * 2. update the includes and _PyImport_FrozenModules[] in this file
 * 3. update the FROZEN_FILES variable in Makefile.pre.in
 * 4. update the per-module targets in Makefile.pre.in
 * 5. update the lists of modules in PCbuild/_freeze_module.vcxproj and
 *    PCbuild/_freeze_module.vcxproj.filters
 *
 * (Note that most of the data in this file is auto-generated by the script.)
 *
 * Those steps can also be done manually, though this is not recommended.
 * Expect such manual changes to be removed the next time
 * freeze_modules.py runs.
 * */

/* In order to test the support for frozen modules, by default we
   define some simple frozen modules: __hello__, __phello__ (a package),
   and __phello__.spam.  Loading any will print some famous words... */

#include "Python.h"

/* Includes for frozen modules: */
#include "frozen_modules/importlib__bootstrap.h"
#include "frozen_modules/importlib__bootstrap_external.h"
#include "frozen_modules/zipimport.h"
#include "frozen_modules/abc.h"
#include "frozen_modules/codecs.h"
#include "frozen_modules/encodings.h"
#include "frozen_modules/encodings___init__.h"
#include "frozen_modules/encodings_aliases.h"
#include "frozen_modules/encodings_ascii.h"
#include "frozen_modules/encodings_base64_codec.h"
#include "frozen_modules/encodings_big5.h"
#include "frozen_modules/encodings_big5hkscs.h"
#include "frozen_modules/encodings_bz2_codec.h"
#include "frozen_modules/encodings_charmap.h"
#include "frozen_modules/encodings_cp037.h"
#include "frozen_modules/encodings_cp1006.h"
#include "frozen_modules/encodings_cp1026.h"
#include "frozen_modules/encodings_cp1125.h"
#include "frozen_modules/encodings_cp1140.h"
#include "frozen_modules/encodings_cp1250.h"
#include "frozen_modules/encodings_cp1251.h"
#include "frozen_modules/encodings_cp1252.h"
#include "frozen_modules/encodings_cp1253.h"
#include "frozen_modules/encodings_cp1254.h"
#include "frozen_modules/encodings_cp1255.h"
#include "frozen_modules/encodings_cp1256.h"
#include "frozen_modules/encodings_cp1257.h"
#include "frozen_modules/encodings_cp1258.h"
#include "frozen_modules/encodings_cp273.h"
#include "frozen_modules/encodings_cp424.h"
#include "frozen_modules/encodings_cp437.h"
#include "frozen_modules/encodings_cp500.h"
#include "frozen_modules/encodings_cp720.h"
#include "frozen_modules/encodings_cp737.h"
#include "frozen_modules/encodings_cp775.h"
#include "frozen_modules/encodings_cp850.h"
#include "frozen_modules/encodings_cp852.h"
#include "frozen_modules/encodings_cp855.h"
#include "frozen_modules/encodings_cp856.h"
#include "frozen_modules/encodings_cp857.h"
#include "frozen_modules/encodings_cp858.h"
#include "frozen_modules/encodings_cp860.h"
#include "frozen_modules/encodings_cp861.h"
#include "frozen_modules/encodings_cp862.h"
#include "frozen_modules/encodings_cp863.h"
#include "frozen_modules/encodings_cp864.h"
#include "frozen_modules/encodings_cp865.h"
#include "frozen_modules/encodings_cp866.h"
#include "frozen_modules/encodings_cp869.h"
#include "frozen_modules/encodings_cp874.h"
#include "frozen_modules/encodings_cp875.h"
#include "frozen_modules/encodings_cp932.h"
#include "frozen_modules/encodings_cp949.h"
#include "frozen_modules/encodings_cp950.h"
#include "frozen_modules/encodings_euc_jis_2004.h"
#include "frozen_modules/encodings_euc_jisx0213.h"
#include "frozen_modules/encodings_euc_jp.h"
#include "frozen_modules/encodings_euc_kr.h"
#include "frozen_modules/encodings_gb18030.h"
#include "frozen_modules/encodings_gb2312.h"
#include "frozen_modules/encodings_gbk.h"
#include "frozen_modules/encodings_hex_codec.h"
#include "frozen_modules/encodings_hp_roman8.h"
#include "frozen_modules/encodings_hz.h"
#include "frozen_modules/encodings_idna.h"
#include "frozen_modules/encodings_iso2022_jp.h"
#include "frozen_modules/encodings_iso2022_jp_1.h"
#include "frozen_modules/encodings_iso2022_jp_2.h"
#include "frozen_modules/encodings_iso2022_jp_2004.h"
#include "frozen_modules/encodings_iso2022_jp_3.h"
#include "frozen_modules/encodings_iso2022_jp_ext.h"
#include "frozen_modules/encodings_iso2022_kr.h"
#include "frozen_modules/encodings_iso8859_1.h"
#include "frozen_modules/encodings_iso8859_10.h"
#include "frozen_modules/encodings_iso8859_11.h"
#include "frozen_modules/encodings_iso8859_13.h"
#include "frozen_modules/encodings_iso8859_14.h"
#include "frozen_modules/encodings_iso8859_15.h"
#include "frozen_modules/encodings_iso8859_16.h"
#include "frozen_modules/encodings_iso8859_2.h"
#include "frozen_modules/encodings_iso8859_3.h"
#include "frozen_modules/encodings_iso8859_4.h"
#include "frozen_modules/encodings_iso8859_5.h"
#include "frozen_modules/encodings_iso8859_6.h"
#include "frozen_modules/encodings_iso8859_7.h"
#include "frozen_modules/encodings_iso8859_8.h"
#include "frozen_modules/encodings_iso8859_9.h"
#include "frozen_modules/encodings_johab.h"
#include "frozen_modules/encodings_koi8_r.h"
#include "frozen_modules/encodings_koi8_t.h"
#include "frozen_modules/encodings_koi8_u.h"
#include "frozen_modules/encodings_kz1048.h"
#include "frozen_modules/encodings_latin_1.h"
#include "frozen_modules/encodings_mac_arabic.h"
#include "frozen_modules/encodings_mac_croatian.h"
#include "frozen_modules/encodings_mac_cyrillic.h"
#include "frozen_modules/encodings_mac_farsi.h"
#include "frozen_modules/encodings_mac_greek.h"
#include "frozen_modules/encodings_mac_iceland.h"
#include "frozen_modules/encodings_mac_latin2.h"
#include "frozen_modules/encodings_mac_roman.h"
#include "frozen_modules/encodings_mac_romanian.h"
#include "frozen_modules/encodings_mac_turkish.h"
#include "frozen_modules/encodings_mbcs.h"
#include "frozen_modules/encodings_oem.h"
#include "frozen_modules/encodings_palmos.h"
#include "frozen_modules/encodings_ptcp154.h"
#include "frozen_modules/encodings_punycode.h"
#include "frozen_modules/encodings_quopri_codec.h"
#include "frozen_modules/encodings_raw_unicode_escape.h"
#include "frozen_modules/encodings_rot_13.h"
#include "frozen_modules/encodings_shift_jis.h"
#include "frozen_modules/encodings_shift_jis_2004.h"
#include "frozen_modules/encodings_shift_jisx0213.h"
#include "frozen_modules/encodings_tis_620.h"
#include "frozen_modules/encodings_undefined.h"
#include "frozen_modules/encodings_unicode_escape.h"
#include "frozen_modules/encodings_utf_16.h"
#include "frozen_modules/encodings_utf_16_be.h"
#include "frozen_modules/encodings_utf_16_le.h"
#include "frozen_modules/encodings_utf_32.h"
#include "frozen_modules/encodings_utf_32_be.h"
#include "frozen_modules/encodings_utf_32_le.h"
#include "frozen_modules/encodings_utf_7.h"
#include "frozen_modules/encodings_utf_8.h"
#include "frozen_modules/encodings_utf_8_sig.h"
#include "frozen_modules/encodings_uu_codec.h"
#include "frozen_modules/encodings_zlib_codec.h"
#include "frozen_modules/io.h"
#include "frozen_modules/_collections_abc.h"
#include "frozen_modules/_sitebuiltins.h"
#include "frozen_modules/genericpath.h"
#include "frozen_modules/posixpath.h"
#include "frozen_modules/os.h"
#include "frozen_modules/site.h"
#include "frozen_modules/stat.h"
#include "frozen_modules/hello.h"
/* End includes */

#ifdef MS_WINDOWS
/* Deepfreeze isn't supported on Windows yet. */
#define GET_CODE(name) NULL
#else
#define GET_CODE(name) _Py_get_##name##_toplevel
#endif

/* Start extern declarations */
extern PyObject *_Py_get_importlib__bootstrap_toplevel(void);
extern PyObject *_Py_get_importlib__bootstrap_external_toplevel(void);
extern PyObject *_Py_get_zipimport_toplevel(void);
extern PyObject *_Py_get_hello_toplevel(void);
extern PyObject *_Py_get_hello_toplevel(void);
extern PyObject *_Py_get_hello_toplevel(void);
/* End extern declarations */

/* Note that a negative size indicates a package. */

static const struct _frozen _PyImport_FrozenModules[] = {
    /* importlib */
    {"_frozen_importlib", _Py_M__importlib__bootstrap, (int)sizeof(_Py_M__importlib__bootstrap), GET_CODE(importlib__bootstrap)},
    {"_frozen_importlib_external", _Py_M__importlib__bootstrap_external, (int)sizeof(_Py_M__importlib__bootstrap_external), GET_CODE(importlib__bootstrap_external)},
    {"zipimport", _Py_M__zipimport, (int)sizeof(_Py_M__zipimport), GET_CODE(zipimport)},

    /* stdlib */
    {"abc", _Py_M__abc, (int)sizeof(_Py_M__abc)},
    {"codecs", _Py_M__codecs, (int)sizeof(_Py_M__codecs)},
    {"encodings", _Py_M__encodings, -(int)sizeof(_Py_M__encodings)},
    {"encodings.__init__", _Py_M__encodings___init__,
        (int)sizeof(_Py_M__encodings___init__)},
    {"encodings.aliases", _Py_M__encodings_aliases,
        (int)sizeof(_Py_M__encodings_aliases)},
    {"encodings.ascii", _Py_M__encodings_ascii,
        (int)sizeof(_Py_M__encodings_ascii)},
    {"encodings.base64_codec", _Py_M__encodings_base64_codec,
        (int)sizeof(_Py_M__encodings_base64_codec)},
    {"encodings.big5", _Py_M__encodings_big5, (int)sizeof(_Py_M__encodings_big5)},
    {"encodings.big5hkscs", _Py_M__encodings_big5hkscs,
        (int)sizeof(_Py_M__encodings_big5hkscs)},
    {"encodings.bz2_codec", _Py_M__encodings_bz2_codec,
        (int)sizeof(_Py_M__encodings_bz2_codec)},
    {"encodings.charmap", _Py_M__encodings_charmap,
        (int)sizeof(_Py_M__encodings_charmap)},
    {"encodings.cp037", _Py_M__encodings_cp037,
        (int)sizeof(_Py_M__encodings_cp037)},
    {"encodings.cp1006", _Py_M__encodings_cp1006,
        (int)sizeof(_Py_M__encodings_cp1006)},
    {"encodings.cp1026", _Py_M__encodings_cp1026,
        (int)sizeof(_Py_M__encodings_cp1026)},
    {"encodings.cp1125", _Py_M__encodings_cp1125,
        (int)sizeof(_Py_M__encodings_cp1125)},
    {"encodings.cp1140", _Py_M__encodings_cp1140,
        (int)sizeof(_Py_M__encodings_cp1140)},
    {"encodings.cp1250", _Py_M__encodings_cp1250,
        (int)sizeof(_Py_M__encodings_cp1250)},
    {"encodings.cp1251", _Py_M__encodings_cp1251,
        (int)sizeof(_Py_M__encodings_cp1251)},
    {"encodings.cp1252", _Py_M__encodings_cp1252,
        (int)sizeof(_Py_M__encodings_cp1252)},
    {"encodings.cp1253", _Py_M__encodings_cp1253,
        (int)sizeof(_Py_M__encodings_cp1253)},
    {"encodings.cp1254", _Py_M__encodings_cp1254,
        (int)sizeof(_Py_M__encodings_cp1254)},
    {"encodings.cp1255", _Py_M__encodings_cp1255,
        (int)sizeof(_Py_M__encodings_cp1255)},
    {"encodings.cp1256", _Py_M__encodings_cp1256,
        (int)sizeof(_Py_M__encodings_cp1256)},
    {"encodings.cp1257", _Py_M__encodings_cp1257,
        (int)sizeof(_Py_M__encodings_cp1257)},
    {"encodings.cp1258", _Py_M__encodings_cp1258,
        (int)sizeof(_Py_M__encodings_cp1258)},
    {"encodings.cp273", _Py_M__encodings_cp273,
        (int)sizeof(_Py_M__encodings_cp273)},
    {"encodings.cp424", _Py_M__encodings_cp424,
        (int)sizeof(_Py_M__encodings_cp424)},
    {"encodings.cp437", _Py_M__encodings_cp437,
        (int)sizeof(_Py_M__encodings_cp437)},
    {"encodings.cp500", _Py_M__encodings_cp500,
        (int)sizeof(_Py_M__encodings_cp500)},
    {"encodings.cp720", _Py_M__encodings_cp720,
        (int)sizeof(_Py_M__encodings_cp720)},
    {"encodings.cp737", _Py_M__encodings_cp737,
        (int)sizeof(_Py_M__encodings_cp737)},
    {"encodings.cp775", _Py_M__encodings_cp775,
        (int)sizeof(_Py_M__encodings_cp775)},
    {"encodings.cp850", _Py_M__encodings_cp850,
        (int)sizeof(_Py_M__encodings_cp850)},
    {"encodings.cp852", _Py_M__encodings_cp852,
        (int)sizeof(_Py_M__encodings_cp852)},
    {"encodings.cp855", _Py_M__encodings_cp855,
        (int)sizeof(_Py_M__encodings_cp855)},
    {"encodings.cp856", _Py_M__encodings_cp856,
        (int)sizeof(_Py_M__encodings_cp856)},
    {"encodings.cp857", _Py_M__encodings_cp857,
        (int)sizeof(_Py_M__encodings_cp857)},
    {"encodings.cp858", _Py_M__encodings_cp858,
        (int)sizeof(_Py_M__encodings_cp858)},
    {"encodings.cp860", _Py_M__encodings_cp860,
        (int)sizeof(_Py_M__encodings_cp860)},
    {"encodings.cp861", _Py_M__encodings_cp861,
        (int)sizeof(_Py_M__encodings_cp861)},
    {"encodings.cp862", _Py_M__encodings_cp862,
        (int)sizeof(_Py_M__encodings_cp862)},
    {"encodings.cp863", _Py_M__encodings_cp863,
        (int)sizeof(_Py_M__encodings_cp863)},
    {"encodings.cp864", _Py_M__encodings_cp864,
        (int)sizeof(_Py_M__encodings_cp864)},
    {"encodings.cp865", _Py_M__encodings_cp865,
        (int)sizeof(_Py_M__encodings_cp865)},
    {"encodings.cp866", _Py_M__encodings_cp866,
        (int)sizeof(_Py_M__encodings_cp866)},
    {"encodings.cp869", _Py_M__encodings_cp869,
        (int)sizeof(_Py_M__encodings_cp869)},
    {"encodings.cp874", _Py_M__encodings_cp874,
        (int)sizeof(_Py_M__encodings_cp874)},
    {"encodings.cp875", _Py_M__encodings_cp875,
        (int)sizeof(_Py_M__encodings_cp875)},
    {"encodings.cp932", _Py_M__encodings_cp932,
        (int)sizeof(_Py_M__encodings_cp932)},
    {"encodings.cp949", _Py_M__encodings_cp949,
        (int)sizeof(_Py_M__encodings_cp949)},
    {"encodings.cp950", _Py_M__encodings_cp950,
        (int)sizeof(_Py_M__encodings_cp950)},
    {"encodings.euc_jis_2004", _Py_M__encodings_euc_jis_2004,
        (int)sizeof(_Py_M__encodings_euc_jis_2004)},
    {"encodings.euc_jisx0213", _Py_M__encodings_euc_jisx0213,
        (int)sizeof(_Py_M__encodings_euc_jisx0213)},
    {"encodings.euc_jp", _Py_M__encodings_euc_jp,
        (int)sizeof(_Py_M__encodings_euc_jp)},
    {"encodings.euc_kr", _Py_M__encodings_euc_kr,
        (int)sizeof(_Py_M__encodings_euc_kr)},
    {"encodings.gb18030", _Py_M__encodings_gb18030,
        (int)sizeof(_Py_M__encodings_gb18030)},
    {"encodings.gb2312", _Py_M__encodings_gb2312,
        (int)sizeof(_Py_M__encodings_gb2312)},
    {"encodings.gbk", _Py_M__encodings_gbk, (int)sizeof(_Py_M__encodings_gbk)},
    {"encodings.hex_codec", _Py_M__encodings_hex_codec,
        (int)sizeof(_Py_M__encodings_hex_codec)},
    {"encodings.hp_roman8", _Py_M__encodings_hp_roman8,
        (int)sizeof(_Py_M__encodings_hp_roman8)},
    {"encodings.hz", _Py_M__encodings_hz, (int)sizeof(_Py_M__encodings_hz)},
    {"encodings.idna", _Py_M__encodings_idna, (int)sizeof(_Py_M__encodings_idna)},
    {"encodings.iso2022_jp", _Py_M__encodings_iso2022_jp,
        (int)sizeof(_Py_M__encodings_iso2022_jp)},
    {"encodings.iso2022_jp_1", _Py_M__encodings_iso2022_jp_1,
        (int)sizeof(_Py_M__encodings_iso2022_jp_1)},
    {"encodings.iso2022_jp_2", _Py_M__encodings_iso2022_jp_2,
        (int)sizeof(_Py_M__encodings_iso2022_jp_2)},
    {"encodings.iso2022_jp_2004", _Py_M__encodings_iso2022_jp_2004,
        (int)sizeof(_Py_M__encodings_iso2022_jp_2004)},
    {"encodings.iso2022_jp_3", _Py_M__encodings_iso2022_jp_3,
        (int)sizeof(_Py_M__encodings_iso2022_jp_3)},
    {"encodings.iso2022_jp_ext", _Py_M__encodings_iso2022_jp_ext,
        (int)sizeof(_Py_M__encodings_iso2022_jp_ext)},
    {"encodings.iso2022_kr", _Py_M__encodings_iso2022_kr,
        (int)sizeof(_Py_M__encodings_iso2022_kr)},
    {"encodings.iso8859_1", _Py_M__encodings_iso8859_1,
        (int)sizeof(_Py_M__encodings_iso8859_1)},
    {"encodings.iso8859_10", _Py_M__encodings_iso8859_10,
        (int)sizeof(_Py_M__encodings_iso8859_10)},
    {"encodings.iso8859_11", _Py_M__encodings_iso8859_11,
        (int)sizeof(_Py_M__encodings_iso8859_11)},
    {"encodings.iso8859_13", _Py_M__encodings_iso8859_13,
        (int)sizeof(_Py_M__encodings_iso8859_13)},
    {"encodings.iso8859_14", _Py_M__encodings_iso8859_14,
        (int)sizeof(_Py_M__encodings_iso8859_14)},
    {"encodings.iso8859_15", _Py_M__encodings_iso8859_15,
        (int)sizeof(_Py_M__encodings_iso8859_15)},
    {"encodings.iso8859_16", _Py_M__encodings_iso8859_16,
        (int)sizeof(_Py_M__encodings_iso8859_16)},
    {"encodings.iso8859_2", _Py_M__encodings_iso8859_2,
        (int)sizeof(_Py_M__encodings_iso8859_2)},
    {"encodings.iso8859_3", _Py_M__encodings_iso8859_3,
        (int)sizeof(_Py_M__encodings_iso8859_3)},
    {"encodings.iso8859_4", _Py_M__encodings_iso8859_4,
        (int)sizeof(_Py_M__encodings_iso8859_4)},
    {"encodings.iso8859_5", _Py_M__encodings_iso8859_5,
        (int)sizeof(_Py_M__encodings_iso8859_5)},
    {"encodings.iso8859_6", _Py_M__encodings_iso8859_6,
        (int)sizeof(_Py_M__encodings_iso8859_6)},
    {"encodings.iso8859_7", _Py_M__encodings_iso8859_7,
        (int)sizeof(_Py_M__encodings_iso8859_7)},
    {"encodings.iso8859_8", _Py_M__encodings_iso8859_8,
        (int)sizeof(_Py_M__encodings_iso8859_8)},
    {"encodings.iso8859_9", _Py_M__encodings_iso8859_9,
        (int)sizeof(_Py_M__encodings_iso8859_9)},
    {"encodings.johab", _Py_M__encodings_johab,
        (int)sizeof(_Py_M__encodings_johab)},
    {"encodings.koi8_r", _Py_M__encodings_koi8_r,
        (int)sizeof(_Py_M__encodings_koi8_r)},
    {"encodings.koi8_t", _Py_M__encodings_koi8_t,
        (int)sizeof(_Py_M__encodings_koi8_t)},
    {"encodings.koi8_u", _Py_M__encodings_koi8_u,
        (int)sizeof(_Py_M__encodings_koi8_u)},
    {"encodings.kz1048", _Py_M__encodings_kz1048,
        (int)sizeof(_Py_M__encodings_kz1048)},
    {"encodings.latin_1", _Py_M__encodings_latin_1,
        (int)sizeof(_Py_M__encodings_latin_1)},
    {"encodings.mac_arabic", _Py_M__encodings_mac_arabic,
        (int)sizeof(_Py_M__encodings_mac_arabic)},
    {"encodings.mac_croatian", _Py_M__encodings_mac_croatian,
        (int)sizeof(_Py_M__encodings_mac_croatian)},
    {"encodings.mac_cyrillic", _Py_M__encodings_mac_cyrillic,
        (int)sizeof(_Py_M__encodings_mac_cyrillic)},
    {"encodings.mac_farsi", _Py_M__encodings_mac_farsi,
        (int)sizeof(_Py_M__encodings_mac_farsi)},
    {"encodings.mac_greek", _Py_M__encodings_mac_greek,
        (int)sizeof(_Py_M__encodings_mac_greek)},
    {"encodings.mac_iceland", _Py_M__encodings_mac_iceland,
        (int)sizeof(_Py_M__encodings_mac_iceland)},
    {"encodings.mac_latin2", _Py_M__encodings_mac_latin2,
        (int)sizeof(_Py_M__encodings_mac_latin2)},
    {"encodings.mac_roman", _Py_M__encodings_mac_roman,
        (int)sizeof(_Py_M__encodings_mac_roman)},
    {"encodings.mac_romanian", _Py_M__encodings_mac_romanian,
        (int)sizeof(_Py_M__encodings_mac_romanian)},
    {"encodings.mac_turkish", _Py_M__encodings_mac_turkish,
        (int)sizeof(_Py_M__encodings_mac_turkish)},
    {"encodings.mbcs", _Py_M__encodings_mbcs, (int)sizeof(_Py_M__encodings_mbcs)},
    {"encodings.oem", _Py_M__encodings_oem, (int)sizeof(_Py_M__encodings_oem)},
    {"encodings.palmos", _Py_M__encodings_palmos,
        (int)sizeof(_Py_M__encodings_palmos)},
    {"encodings.ptcp154", _Py_M__encodings_ptcp154,
        (int)sizeof(_Py_M__encodings_ptcp154)},
    {"encodings.punycode", _Py_M__encodings_punycode,
        (int)sizeof(_Py_M__encodings_punycode)},
    {"encodings.quopri_codec", _Py_M__encodings_quopri_codec,
        (int)sizeof(_Py_M__encodings_quopri_codec)},
    {"encodings.raw_unicode_escape", _Py_M__encodings_raw_unicode_escape,
        (int)sizeof(_Py_M__encodings_raw_unicode_escape)},
    {"encodings.rot_13", _Py_M__encodings_rot_13,
        (int)sizeof(_Py_M__encodings_rot_13)},
    {"encodings.shift_jis", _Py_M__encodings_shift_jis,
        (int)sizeof(_Py_M__encodings_shift_jis)},
    {"encodings.shift_jis_2004", _Py_M__encodings_shift_jis_2004,
        (int)sizeof(_Py_M__encodings_shift_jis_2004)},
    {"encodings.shift_jisx0213", _Py_M__encodings_shift_jisx0213,
        (int)sizeof(_Py_M__encodings_shift_jisx0213)},
    {"encodings.tis_620", _Py_M__encodings_tis_620,
        (int)sizeof(_Py_M__encodings_tis_620)},
    {"encodings.undefined", _Py_M__encodings_undefined,
        (int)sizeof(_Py_M__encodings_undefined)},
    {"encodings.unicode_escape", _Py_M__encodings_unicode_escape,
        (int)sizeof(_Py_M__encodings_unicode_escape)},
    {"encodings.utf_16", _Py_M__encodings_utf_16,
        (int)sizeof(_Py_M__encodings_utf_16)},
    {"encodings.utf_16_be", _Py_M__encodings_utf_16_be,
        (int)sizeof(_Py_M__encodings_utf_16_be)},
    {"encodings.utf_16_le", _Py_M__encodings_utf_16_le,
        (int)sizeof(_Py_M__encodings_utf_16_le)},
    {"encodings.utf_32", _Py_M__encodings_utf_32,
        (int)sizeof(_Py_M__encodings_utf_32)},
    {"encodings.utf_32_be", _Py_M__encodings_utf_32_be,
        (int)sizeof(_Py_M__encodings_utf_32_be)},
    {"encodings.utf_32_le", _Py_M__encodings_utf_32_le,
        (int)sizeof(_Py_M__encodings_utf_32_le)},
    {"encodings.utf_7", _Py_M__encodings_utf_7,
        (int)sizeof(_Py_M__encodings_utf_7)},
    {"encodings.utf_8", _Py_M__encodings_utf_8,
        (int)sizeof(_Py_M__encodings_utf_8)},
    {"encodings.utf_8_sig", _Py_M__encodings_utf_8_sig,
        (int)sizeof(_Py_M__encodings_utf_8_sig)},
    {"encodings.uu_codec", _Py_M__encodings_uu_codec,
        (int)sizeof(_Py_M__encodings_uu_codec)},
    {"encodings.zlib_codec", _Py_M__encodings_zlib_codec,
        (int)sizeof(_Py_M__encodings_zlib_codec)},
    {"io", _Py_M__io, (int)sizeof(_Py_M__io)},
    {"_collections_abc", _Py_M___collections_abc,
        (int)sizeof(_Py_M___collections_abc)},
    {"_sitebuiltins", _Py_M___sitebuiltins, (int)sizeof(_Py_M___sitebuiltins)},
    {"genericpath", _Py_M__genericpath, (int)sizeof(_Py_M__genericpath)},
    {"posixpath", _Py_M__posixpath, (int)sizeof(_Py_M__posixpath)},
    {"os", _Py_M__os, (int)sizeof(_Py_M__os)},
    {"site", _Py_M__site, (int)sizeof(_Py_M__site)},
    {"stat", _Py_M__stat, (int)sizeof(_Py_M__stat)},

    /* Test module */
    {"__hello__", _Py_M__hello, (int)sizeof(_Py_M__hello), GET_CODE(hello)},
    {"__phello__", _Py_M__hello, -(int)sizeof(_Py_M__hello), GET_CODE(hello)},
    {"__phello__.spam", _Py_M__hello, (int)sizeof(_Py_M__hello), GET_CODE(hello)},
    {0, 0, 0} /* sentinel */
};

/* Embedding apps may change this pointer to point to their favorite
   collection of frozen modules: */

const struct _frozen *PyImport_FrozenModules = _PyImport_FrozenModules;
