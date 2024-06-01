#include "Python.h"
#include "pycore_abstract.h"   // _PyIndex_Check()
#include "pycore_bytes_methods.h"

PyDoc_STRVAR_shared(_Py_isspace__doc__,
"B.isspace() -> bool\n\
\n\
Return True if all characters in B are whitespace\n\
and there is at least one character in B, False otherwise.");

PyObject*
_Py_bytes_isspace(const char *cptr, Py_ssize_t len)
{
    const unsigned char *p
        = (const unsigned char *) cptr;
    const unsigned char *e;

    /* Shortcut for single character strings */
    if (len == 1 && Py_ISSPACE(*p))
        Py_RETURN_TRUE;

    /* Special case for empty strings */
    if (len == 0)
        Py_RETURN_FALSE;

    e = p + len;
    for (; p < e; p++) {
        if (!Py_ISSPACE(*p))
            Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}


PyDoc_STRVAR_shared(_Py_isalpha__doc__,
"B.isalpha() -> bool\n\
\n\
Return True if all characters in B are alphabetic\n\
and there is at least one character in B, False otherwise.");

PyObject*
_Py_bytes_isalpha(const char *cptr, Py_ssize_t len)
{
    const unsigned char *p
        = (const unsigned char *) cptr;
    const unsigned char *e;

    /* Shortcut for single character strings */
    if (len == 1 && Py_ISALPHA(*p))
        Py_RETURN_TRUE;

    /* Special case for empty strings */
    if (len == 0)
        Py_RETURN_FALSE;

    e = p + len;
    for (; p < e; p++) {
        if (!Py_ISALPHA(*p))
            Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}


PyDoc_STRVAR_shared(_Py_isalnum__doc__,
"B.isalnum() -> bool\n\
\n\
Return True if all characters in B are alphanumeric\n\
and there is at least one character in B, False otherwise.");

PyObject*
_Py_bytes_isalnum(const char *cptr, Py_ssize_t len)
{
    const unsigned char *p
        = (const unsigned char *) cptr;
    const unsigned char *e;

    /* Shortcut for single character strings */
    if (len == 1 && Py_ISALNUM(*p))
        Py_RETURN_TRUE;

    /* Special case for empty strings */
    if (len == 0)
        Py_RETURN_FALSE;

    e = p + len;
    for (; p < e; p++) {
        if (!Py_ISALNUM(*p))
            Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}


PyDoc_STRVAR_shared(_Py_isascii__doc__,
"B.isascii() -> bool\n\
\n\
Return True if B is empty or all characters in B are ASCII,\n\
False otherwise.");

// Optimization is copied from ascii_decode in unicodeobject.c
/* Mask to quickly check whether a C 'size_t' contains a
   non-ASCII, UTF8-encoded char. */
#if (SIZEOF_SIZE_T == 8)
# define ASCII_CHAR_MASK 0x8080808080808080ULL
#elif (SIZEOF_SIZE_T == 4)
# define ASCII_CHAR_MASK 0x80808080U
#else
# error C 'size_t' size should be either 4 or 8!
#endif

PyObject*
_Py_bytes_isascii(const char *cptr, Py_ssize_t len)
{
    const char *p = cptr;
    const char *end = p + len;

    while (p < end) {
        /* Fast path, see in STRINGLIB(utf8_decode) in stringlib/codecs.h
           for an explanation. */
        if (_Py_IS_ALIGNED(p, ALIGNOF_SIZE_T)) {
            /* Help allocation */
            const char *_p = p;
            while (_p + SIZEOF_SIZE_T <= end) {
                size_t value = *(const size_t *) _p;
                if (value & ASCII_CHAR_MASK) {
                    Py_RETURN_FALSE;
                }
                _p += SIZEOF_SIZE_T;
            }
            p = _p;
            if (_p == end)
                break;
        }
        if ((unsigned char)*p & 0x80) {
            Py_RETURN_FALSE;
        }
        p++;
    }
    Py_RETURN_TRUE;
}

#undef ASCII_CHAR_MASK


PyDoc_STRVAR_shared(_Py_isdigit__doc__,
"B.isdigit() -> bool\n\
\n\
Return True if all characters in B are digits\n\
and there is at least one character in B, False otherwise.");

PyObject*
_Py_bytes_isdigit(const char *cptr, Py_ssize_t len)
{
    const unsigned char *p
        = (const unsigned char *) cptr;
    const unsigned char *e;

    /* Shortcut for single character strings */
    if (len == 1 && Py_ISDIGIT(*p))
        Py_RETURN_TRUE;

    /* Special case for empty strings */
    if (len == 0)
        Py_RETURN_FALSE;

    e = p + len;
    for (; p < e; p++) {
        if (!Py_ISDIGIT(*p))
            Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}


PyDoc_STRVAR_shared(_Py_islower__doc__,
"B.islower() -> bool\n\
\n\
Return True if all cased characters in B are lowercase and there is\n\
at least one cased character in B, False otherwise.");

PyObject*
_Py_bytes_islower(const char *cptr, Py_ssize_t len)
{
    const unsigned char *p
        = (const unsigned char *) cptr;
    const unsigned char *e;
    int cased;

    /* Shortcut for single character strings */
    if (len == 1)
        return PyBool_FromLong(Py_ISLOWER(*p));

    /* Special case for empty strings */
    if (len == 0)
        Py_RETURN_FALSE;

    e = p + len;
    cased = 0;
    for (; p < e; p++) {
        if (Py_ISUPPER(*p))
            Py_RETURN_FALSE;
        else if (!cased && Py_ISLOWER(*p))
            cased = 1;
    }
    return PyBool_FromLong(cased);
}


PyDoc_STRVAR_shared(_Py_isupper__doc__,
"B.isupper() -> bool\n\
\n\
Return True if all cased characters in B are uppercase and there is\n\
at least one cased character in B, False otherwise.");

PyObject*
_Py_bytes_isupper(const char *cptr, Py_ssize_t len)
{
    const unsigned char *p
        = (const unsigned char *) cptr;
    const unsigned char *e;
    int cased;

    /* Shortcut for single character strings */
    if (len == 1)
        return PyBool_FromLong(Py_ISUPPER(*p));

    /* Special case for empty strings */
    if (len == 0)
        Py_RETURN_FALSE;

    e = p + len;
    cased = 0;
    for (; p < e; p++) {
        if (Py_ISLOWER(*p))
            Py_RETURN_FALSE;
        else if (!cased && Py_ISUPPER(*p))
            cased = 1;
    }
    return PyBool_FromLong(cased);
}


PyDoc_STRVAR_shared(_Py_istitle__doc__,
"B.istitle() -> bool\n\
\n\
Return True if B is a titlecased string and there is at least one\n\
character in B, i.e. uppercase characters may only follow uncased\n\
characters and lowercase characters only cased ones. Return False\n\
otherwise.");

PyObject*
_Py_bytes_istitle(const char *cptr, Py_ssize_t len)
{
    const unsigned char *p
        = (const unsigned char *) cptr;
    const unsigned char *e;
    int cased, previous_is_cased;

    if (len == 1) {
        if (Py_ISUPPER(*p)) {
            Py_RETURN_TRUE;
        }
        Py_RETURN_FALSE;
    }

    /* Special case for empty strings */
    if (len == 0)
        Py_RETURN_FALSE;

    e = p + len;
    cased = 0;
    previous_is_cased = 0;
    for (; p < e; p++) {
        const unsigned char ch = *p;

        if (Py_ISUPPER(ch)) {
            if (previous_is_cased)
                Py_RETURN_FALSE;
            previous_is_cased = 1;
            cased = 1;
        }
        else if (Py_ISLOWER(ch)) {
            if (!previous_is_cased)
                Py_RETURN_FALSE;
            previous_is_cased = 1;
            cased = 1;
        }
        else
            previous_is_cased = 0;
    }
    return PyBool_FromLong(cased);
}


PyDoc_STRVAR_shared(_Py_lower__doc__,
"B.lower() -> copy of B\n\
\n\
Return a copy of B with all ASCII characters converted to lowercase.");

void
_Py_bytes_lower(char *result, const char *cptr, Py_ssize_t len)
{
    Py_ssize_t i;

    for (i = 0; i < len; i++) {
        result[i] = Py_TOLOWER((unsigned char) cptr[i]);
    }
}


PyDoc_STRVAR_shared(_Py_upper__doc__,
"B.upper() -> copy of B\n\
\n\
Return a copy of B with all ASCII characters converted to uppercase.");

void
_Py_bytes_upper(char *result, const char *cptr, Py_ssize_t len)
{
    Py_ssize_t i;

    for (i = 0; i < len; i++) {
        result[i] = Py_TOUPPER((unsigned char) cptr[i]);
    }
}


PyDoc_STRVAR_shared(_Py_title__doc__,
"B.title() -> copy of B\n\
\n\
Return a titlecased version of B, i.e. ASCII words start with uppercase\n\
characters, all remaining cased characters have lowercase.");

void
_Py_bytes_title(char *result, const char *s, Py_ssize_t len)
{
    Py_ssize_t i;
    int previous_is_cased = 0;

    for (i = 0; i < len; i++) {
        int c = Py_CHARMASK(*s++);
        if (Py_ISLOWER(c)) {
            if (!previous_is_cased)
                c = Py_TOUPPER(c);
            previous_is_cased = 1;
        } else if (Py_ISUPPER(c)) {
            if (previous_is_cased)
                c = Py_TOLOWER(c);
            previous_is_cased = 1;
        } else
            previous_is_cased = 0;
        *result++ = c;
    }
}


PyDoc_STRVAR_shared(_Py_capitalize__doc__,
"B.capitalize() -> copy of B\n\
\n\
Return a copy of B with only its first character capitalized (ASCII)\n\
and the rest lower-cased.");

void
_Py_bytes_capitalize(char *result, const char *s, Py_ssize_t len)
{
    if (len > 0) {
        *result = Py_TOUPPER(*s);
        _Py_bytes_lower(result + 1, s + 1, len - 1);
    }
}


PyDoc_STRVAR_shared(_Py_swapcase__doc__,
"B.swapcase() -> copy of B\n\
\n\
Return a copy of B with uppercase ASCII characters converted\n\
to lowercase ASCII and vice versa.");

void
_Py_bytes_swapcase(char *result, const char *s, Py_ssize_t len)
{
    Py_ssize_t i;

    for (i = 0; i < len; i++) {
        int c = Py_CHARMASK(*s++);
        if (Py_ISLOWER(c)) {
            *result = Py_TOUPPER(c);
        }
        else if (Py_ISUPPER(c)) {
            *result = Py_TOLOWER(c);
        }
        else
            *result = c;
        result++;
    }
}


PyDoc_STRVAR_shared(_Py_maketrans__doc__,
"B.maketrans(frm, to) -> translation table\n\
\n\
Return a translation table (a bytes object of length 256) suitable\n\
for use in the bytes or bytearray translate method where each byte\n\
in frm is mapped to the byte at the same position in to.\n\
The bytes objects frm and to must be of the same length.");

PyObject *
_Py_bytes_maketrans(Py_buffer *frm, Py_buffer *to)
{
    PyObject *res = NULL;
    Py_ssize_t i;
    char *p;

    if (frm->len != to->len) {
        PyErr_Format(PyExc_ValueError,
                     "maketrans arguments must have same length");
        return NULL;
    }
    res = PyBytes_FromStringAndSize(NULL, 256);
    if (!res)
        return NULL;
    p = PyBytes_AS_STRING(res);
    for (i = 0; i < 256; i++)
        p[i] = (char) i;
    for (i = 0; i < frm->len; i++) {
        p[((unsigned char *)frm->buf)[i]] = ((char *)to->buf)[i];
    }

    return res;
}

#define FASTSEARCH fastsearch
#define STRINGLIB(F) stringlib_##F
#define STRINGLIB_CHAR char
#define STRINGLIB_SIZEOF_CHAR 1
#define STRINGLIB_FAST_MEMCHR memchr

#include "stringlib/fastsearch.h"
#include "stringlib/count.h"
#include "stringlib/find.h"

/*
Wraps stringlib_parse_args_finds() and additionally checks the first
argument type.

In case the first argument is a bytes-like object, sets it to subobj,
and doesn't touch the byte parameter.
In case it is an integer in range(0, 256), writes the integer value
to byte, and sets subobj to NULL.

The other parameters are similar to those of
stringlib_parse_args_finds().
*/

Py_LOCAL_INLINE(int)
parse_args_finds_byte(const char *function_name, PyObject **subobj, char *byte)
{
    if (PyObject_CheckBuffer(*subobj)) {
        return 1;
    }

    if (!_PyIndex_Check(*subobj)) {
        PyErr_Format(PyExc_TypeError,
                     "argument should be integer or bytes-like object, "
                     "not '%.200s'",
                     Py_TYPE(*subobj)->tp_name);
        return 0;
    }

    Py_ssize_t ival = PyNumber_AsSsize_t(*subobj, NULL);
    if (ival == -1 && PyErr_Occurred()) {
        return 0;
    }
    if (ival < 0 || ival > 255) {
        PyErr_SetString(PyExc_ValueError, "byte must be in range(0, 256)");
        return 0;
    }

    *subobj = NULL;
    *byte = (char)ival;
    return 1;
}

/* helper macro to fixup start/end slice values */
#define ADJUST_INDICES(start, end, len)         \
    if (end > len)                          \
        end = len;                          \
    else if (end < 0) {                     \
        end += len;                         \
        if (end < 0)                        \
        end = 0;                        \
    }                                       \
    if (start < 0) {                        \
        start += len;                       \
        if (start < 0)                      \
        start = 0;                      \
    }

Py_ssize_t
fast_find_internal(const char *str, Py_ssize_t len,
                   const char *sub, Py_ssize_t sub_len,
                   Py_ssize_t start, Py_ssize_t end,
                   int direction)
{
    if (end - start < sub_len)
        return -1;
    else if (sub_len == 1) {
        Py_ssize_t res;
        if (direction > 0)
            res = stringlib_find_char(str + start, end - start, *sub);
        else
            res = stringlib_rfind_char(str + start, end - start, *sub);
        if (res >= 0)
            res += start;
        return res;
    }
    else {
        if (direction > 0)
            return stringlib_find_slice(str, len, sub, sub_len, start, end);
        else
            return stringlib_rfind_slice(str, len, sub, sub_len, start, end);
    }
}

Py_LOCAL_INLINE(Py_ssize_t)
find_internal(const char *str, Py_ssize_t len,
              const char *function_name, PyObject *subobj,
              Py_ssize_t start, Py_ssize_t end,
              int direction)
{
    char byte;
    Py_buffer subbuf;
    const char *sub;
    Py_ssize_t sub_len;

    if (!parse_args_finds_byte(function_name, &subobj, &byte)) {
        return -2;
    }

    if (subobj) {
        if (PyObject_GetBuffer(subobj, &subbuf, PyBUF_SIMPLE) != 0)
            return -2;

        sub = subbuf.buf;
        sub_len = subbuf.len;
    }
    else {
        sub = &byte;
        sub_len = 1;
    }

    ADJUST_INDICES(start, end, len);
    Py_ssize_t res = fast_find_internal(str, len, sub, sub_len, start, end,
                                        direction);

    if (subobj)
        PyBuffer_Release(&subbuf);

    return res;
}

#define FIND_CHUNK_SIZE 1000
#define RFIND_CHUNK_SIZE FIND_CHUNK_SIZE

static Py_ssize_t
find_first_internal(const char *str, Py_ssize_t len, const char *function_name,
                    PyObject *subobj, Py_ssize_t start, Py_ssize_t end,
                    int direction)
{
    if (!PyTuple_Check(subobj)) {
        return find_internal(str, len, function_name, subobj, start, end,
                             direction);
    }
    Py_ssize_t tuple_len = PyTuple_GET_SIZE(subobj);
    if (tuple_len == 0) {
        return -1;
    }
    if (tuple_len == 1) {
        PyObject *subseq = PyTuple_GET_ITEM(subobj, 0);
        return find_internal(str, len, function_name, subseq, start, end,
                             direction);
    }
    if ((size_t)tuple_len > (size_t)PY_SSIZE_T_MAX / sizeof(char) ||
        (size_t)tuple_len > (size_t)PY_SSIZE_T_MAX / sizeof(char *) ||
        (size_t)tuple_len > (size_t)PY_SSIZE_T_MAX / sizeof(Py_ssize_t))
    {
        PyErr_SetString(PyExc_OverflowError, "tuple is too long");
        return -2;
    }
    char *bytes = PyMem_RawMalloc(((size_t)tuple_len) * sizeof(char));
    const char **subs = NULL;
    Py_ssize_t *sub_lengths = NULL;
    if (!bytes) {
        PyErr_NoMemory();
        return -2;
    }
    subs = PyMem_RawMalloc(((size_t)tuple_len) * sizeof(char *));
    if (!subs) {
        PyErr_NoMemory();
        return -2;
    }
    sub_lengths = PyMem_RawMalloc(((size_t)tuple_len) * sizeof(Py_ssize_t));
    if (!sub_lengths) {
        PyErr_NoMemory();
        return -2;
    }
    Py_ssize_t result = -1;
    for (Py_ssize_t i = 0; i < tuple_len; i++) {
        PyObject *subseq = PyTuple_GET_ITEM(subobj, i);
        char byte = bytes[i];
        Py_buffer subbuf;
        const char *sub;
        Py_ssize_t sub_len;
        if (!parse_args_finds_byte(function_name, &subseq, &byte)) {
            return -2;
        }
        else if (subseq) {
            if (PyObject_GetBuffer(subseq, &subbuf, PyBUF_SIMPLE) != 0) {
                return -2;
            }
            sub = subbuf.buf;
            sub_len = subbuf.len;
            PyBuffer_Release(&subbuf);
        }
        else {
            sub = &byte;
            sub_len = 1;
        }
        subs[i] = sub;
        sub_lengths[i] = sub_len;
    }
    ADJUST_INDICES(start, end, len);
    if (direction > 0) {
        assert(FIND_CHUNK_SIZE > 0);
        for (; result == -1; start += FIND_CHUNK_SIZE) {
            Py_ssize_t cur_end;
            if (start > end - FIND_CHUNK_SIZE + 1) { // Guard overflow
                cur_end = end;
            }
            else {
                cur_end = start - 1 + FIND_CHUNK_SIZE;
            }
            for (Py_ssize_t i = 0; i < tuple_len; i++) {
                const char *sub = subs[i];
                Py_ssize_t sub_len = sub_lengths[i];
                Py_ssize_t new_result;
                if (cur_end >= end - sub_len) { // Guard overflow
                    new_result = fast_find_internal(str, len, sub, sub_len,
                                                    start, end, +1);
                }
                else {
                    new_result = fast_find_internal(str, len, sub, sub_len,
                                                    start, cur_end + sub_len,
                                                    +1);
                }
                if (new_result == -2) {
                    result = -2;
                    goto exit;
                }
                if (new_result != -1) {
                    if (new_result == start) {
                        result = start;
                        goto exit;
                    }
                    cur_end = new_result - 1;
                    result = new_result;
                }
            }
            if (start > end - FIND_CHUNK_SIZE) {
                break; // Guard overflow
            }
        }
    }
    else {
        Py_ssize_t cur_end = end;
        assert(RFIND_CHUNK_SIZE > 0);
        for (; result == -1 && cur_end >= start; cur_end -= RFIND_CHUNK_SIZE) {
            Py_ssize_t cur_start = cur_end - RFIND_CHUNK_SIZE + 1;
            if (cur_start < start) {
                cur_start = start;
            }
            for (Py_ssize_t i = 0; i < tuple_len; i++) {
                const char *sub = subs[i];
                Py_ssize_t sub_len = sub_lengths[i];
                Py_ssize_t new_result;
                if (cur_end >= end - sub_len) { // Guard overflow
                    new_result = fast_find_internal(str, len, sub, sub_len,
                                                    cur_start, end, -1);
                }
                else {
                    new_result = fast_find_internal(str, len, sub, sub_len,
                                                    cur_start,
                                                    cur_end + sub_len, -1);
                }
                if (new_result == -2) {
                    result = -2;
                    goto exit;
                }
                if (new_result != -1) {
                    if (new_result == cur_end) {
                        result = cur_end;
                        goto exit;
                    }
                    cur_start = new_result + 1;
                    result = new_result;
                }
            }
        }
    }
exit:
    PyMem_RawFree(bytes);
    PyMem_RawFree(subs);
    PyMem_RawFree(sub_lengths);
    return result;
}

PyObject *
_Py_bytes_find(const char *str, Py_ssize_t len, PyObject *subobj,
               Py_ssize_t start, Py_ssize_t end)
{
    Py_ssize_t result = find_first_internal(str, len, "find", subobj, start,
                                            end, +1);
    return result == -2 ? NULL : PyLong_FromSsize_t(result);
}

PyObject *
_Py_bytes_index(const char *str, Py_ssize_t len, PyObject *subobj,
                Py_ssize_t start, Py_ssize_t end)
{
    Py_ssize_t result = find_first_internal(str, len, "index", subobj, start,
                                            end, +1);
    if (result == -1) {
        PyErr_SetString(PyExc_ValueError, "subsection not found");
    }
    return result < 0 ? NULL : PyLong_FromSsize_t(result);
}

PyObject *
_Py_bytes_rfind(const char *str, Py_ssize_t len, PyObject *subobj,
                Py_ssize_t start, Py_ssize_t end)
{
    Py_ssize_t result = find_first_internal(str, len, "rfind", subobj, start,
                                            end, -1);
    return result == -2 ? NULL : PyLong_FromSsize_t(result);
}

PyObject *
_Py_bytes_rindex(const char *str, Py_ssize_t len, PyObject *subobj,
                 Py_ssize_t start, Py_ssize_t end)
{
    Py_ssize_t result = find_first_internal(str, len, "rindex", subobj, start,
                                            end, -1);
    if (result == -1) {
        PyErr_SetString(PyExc_ValueError, "subsection not found");
    }
    return result < 0 ? NULL : PyLong_FromSsize_t(result);
}

PyObject *
_Py_bytes_count(const char *str, Py_ssize_t len, PyObject *sub_obj,
                Py_ssize_t start, Py_ssize_t end)
{
    const char *sub;
    Py_ssize_t sub_len;
    char byte;

    Py_buffer vsub;
    PyObject *count_obj;

    if (!parse_args_finds_byte("count", &sub_obj, &byte)) {
        return NULL;
    }

    if (sub_obj) {
        if (PyObject_GetBuffer(sub_obj, &vsub, PyBUF_SIMPLE) != 0)
            return NULL;

        sub = vsub.buf;
        sub_len = vsub.len;
    }
    else {
        sub = &byte;
        sub_len = 1;
    }

    ADJUST_INDICES(start, end, len);

    count_obj = PyLong_FromSsize_t(
        stringlib_count(str + start, end - start, sub, sub_len, PY_SSIZE_T_MAX)
        );

    if (sub_obj)
        PyBuffer_Release(&vsub);

    return count_obj;
}

int
_Py_bytes_contains(const char *str, Py_ssize_t len, PyObject *arg)
{
    Py_ssize_t ival = PyNumber_AsSsize_t(arg, NULL);
    if (ival == -1 && PyErr_Occurred()) {
        Py_buffer varg;
        Py_ssize_t pos;
        PyErr_Clear();
        if (PyObject_GetBuffer(arg, &varg, PyBUF_SIMPLE) != 0)
            return -1;
        pos = stringlib_find(str, len,
                             varg.buf, varg.len, 0);
        PyBuffer_Release(&varg);
        return pos >= 0;
    }
    if (ival < 0 || ival >= 256) {
        PyErr_SetString(PyExc_ValueError, "byte must be in range(0, 256)");
        return -1;
    }

    return memchr(str, (int) ival, len) != NULL;
}


/* Matches the end (direction >= 0) or start (direction < 0) of the buffer
 * against substr, using the start and end arguments. Returns
 * -1 on error, 0 if not found and 1 if found.
 */
static int
tailmatch(const char *str, Py_ssize_t len, PyObject *substr,
          Py_ssize_t start, Py_ssize_t end, int direction)
{
    Py_buffer sub_view = {NULL, NULL};
    const char *sub;
    Py_ssize_t slen;

    if (PyBytes_Check(substr)) {
        sub = PyBytes_AS_STRING(substr);
        slen = PyBytes_GET_SIZE(substr);
    }
    else {
        if (PyObject_GetBuffer(substr, &sub_view, PyBUF_SIMPLE) != 0)
            return -1;
        sub = sub_view.buf;
        slen = sub_view.len;
    }

    ADJUST_INDICES(start, end, len);

    if (direction < 0) {
        /* startswith */
        if (start > len - slen)
            goto notfound;
    } else {
        /* endswith */
        if (end - start < slen || start > len)
            goto notfound;

        if (end - slen > start)
            start = end - slen;
    }
    if (end - start < slen)
        goto notfound;
    if (memcmp(str + start, sub, slen) != 0)
        goto notfound;

    PyBuffer_Release(&sub_view);
    return 1;

notfound:
    PyBuffer_Release(&sub_view);
    return 0;
}

static PyObject *
_Py_bytes_tailmatch(const char *str, Py_ssize_t len,
                    const char *function_name, PyObject *subobj,
                    Py_ssize_t start, Py_ssize_t end,
                    int direction)
{
    if (PyTuple_Check(subobj)) {
        Py_ssize_t i;
        for (i = 0; i < PyTuple_GET_SIZE(subobj); i++) {
            PyObject *item = PyTuple_GET_ITEM(subobj, i);
            int result = tailmatch(str, len, item, start, end, direction);
            if (result < 0) {
                return NULL;
            }
            else if (result) {
                Py_RETURN_TRUE;
            }
        }
        Py_RETURN_FALSE;
    }
    int result = tailmatch(str, len, subobj, start, end, direction);
    if (result == -1) {
        if (PyErr_ExceptionMatches(PyExc_TypeError)) {
            PyErr_Format(PyExc_TypeError,
                         "%s first arg must be bytes or a tuple of bytes, "
                         "not %s",
                         function_name, Py_TYPE(subobj)->tp_name);
        }
        return NULL;
    }
    return PyBool_FromLong(result);
}

PyObject *
_Py_bytes_startswith(const char *str, Py_ssize_t len, PyObject *subobj,
                     Py_ssize_t start, Py_ssize_t end)
{
    return _Py_bytes_tailmatch(str, len, "startswith", subobj, start, end, -1);
}

PyObject *
_Py_bytes_endswith(const char *str, Py_ssize_t len, PyObject *subobj,
                   Py_ssize_t start, Py_ssize_t end)
{
    return _Py_bytes_tailmatch(str, len, "endswith", subobj, start, end, +1);
}
