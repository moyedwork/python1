#ifndef Py_BUILD_CORE_BUILTIN
#  define Py_BUILD_CORE_MODULE 1
#endif

#include "Python.h"
// windows.h must be included before pycore internal headers
#ifdef MS_WIN32
#  include <windows.h>
#endif

#include "pycore_bitutils.h"      // _Py_bswap32()
#include "pycore_call.h"          // _PyObject_CallNoArgs()

#include <ffi.h>
#include "ctypes.h"


#define CTYPES_CFIELD_CAPSULE_NAME_PYMEM "_ctypes/cfield.c pymem"

static void pymem_destructor(PyObject *ptr)
{
    void *p = PyCapsule_GetPointer(ptr, CTYPES_CFIELD_CAPSULE_NAME_PYMEM);
    if (p) {
        PyMem_Free(p);
    }
}


/******************************************************************/
/*
  PyCField_Type
*/
static PyObject *
PyCField_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    CFieldObject *obj;
    obj = (CFieldObject *)type->tp_alloc(type, 0);
    return (PyObject *)obj;
}

static inline
Py_ssize_t round_down(Py_ssize_t numToRound, Py_ssize_t multiple)
{
    assert(numToRound >= 0);
    if (multiple == 0)
        return numToRound;
    return (numToRound / multiple) * multiple;
}

static inline
Py_ssize_t round_up(Py_ssize_t numToRound, Py_ssize_t multiple)
{
    assert(numToRound >= 0);
    if (multiple == 0)
        return numToRound;
    return ((numToRound + multiple - 1) / multiple) * multiple;
}

static inline
Py_ssize_t NUM_BITS(Py_ssize_t bitsize);
static inline
Py_ssize_t LOW_BIT(Py_ssize_t offset);
static inline
Py_ssize_t BUILD_SIZE(Py_ssize_t bitsize, Py_ssize_t offset);

/*
 * Expects the size, index and offset for the current field in *psize and
 * *poffset, stores the total size so far in *psize, the offset for the next
 * field in *poffset, the alignment requirements for the current field in
 * *palign, and returns a field descriptor for this field.
 */
/*
 * bitfields extension:
 * bitsize != 0: this is a bit field.
 * pbitofs points to the current bit offset, this will be updated.
 * prev_desc points to the type of the previous bitfield, if any.
 */

void
PyCField_FromDesc_linux(PyObject *desc, Py_ssize_t index,
                Py_ssize_t *pfield_size, int bitsize, Py_ssize_t *pbitofs,
                Py_ssize_t *psize, Py_ssize_t *poffset, Py_ssize_t *palign,
                int pack, int big_endian,
                CFieldObject* self, StgDictObject* dict,
                int is_bitfield
                )
{
    assert(*pfield_size == 0);
    *pbitofs += *poffset * 8;
    *poffset = 0;

    *palign = dict->align;

    if ((bitsize > 0)
         && (round_down(*pbitofs, 8 * dict->align)
            < round_down(*pbitofs + bitsize - 1, 8 * dict->align))) {
        // We would be straddling alignment units.
        *pbitofs = round_up(*pbitofs, 8*dict->align);
    }

    assert(bitsize <= dict->size * 8);
    assert(*poffset == 0);

    // We need to fit within alignment and within size.
    // But we only really care about size, when we have a bitfield.
    if(is_bitfield) {
        self->offset = round_down(*pbitofs, 8*dict->size) / 8;
        Py_ssize_t effective_bitsof = *pbitofs - 8 * self->offset;
        self->size = BUILD_SIZE(bitsize, effective_bitsof);
        assert(dict->size == dict->align);
        assert(effective_bitsof <= dict->size * 8);
    } else {
        self->offset = round_down(*pbitofs, 8*dict->align) / 8;
        self->size = dict->size;
    }

    *pbitofs += bitsize;
    *psize = round_up(*pbitofs, 8) / 8;

    assert(!is_bitfield || (LOW_BIT(self->size) <= self->size * 8));
}

void
PyCField_FromDesc_windows(PyObject *desc, Py_ssize_t index,
                Py_ssize_t *pfield_size, int bitsize, Py_ssize_t *pbitofs,
                Py_ssize_t *psize, Py_ssize_t *poffset, Py_ssize_t *palign,
                int pack, int big_endian,
                CFieldObject* self, StgDictObject* dict,
                int is_bitfield
                )
{
    Py_ssize_t align;
    if (pack)
        align = min(pack, dict->align);
    else
        align = dict->align;

    assert(bitsize <= dict->size * 8);

    // New thing: poffset points to end of bitfield.
    // And we work with negative *pbitofs;
    if (0 < *pbitofs + bitsize || 8 * dict->size != *pfield_size) {
        // Close bitfield, ...
        // ... align,
        *poffset = round_up(*poffset, align);

        // ... and re-open.
        *poffset += dict->size;

        *pfield_size = dict->size * 8;
        *pbitofs = - *pfield_size;
    }

    assert(8 * dict->size == *pfield_size);

    // We need to fit within alignment and within size.
    // But we only really care about size, when we have a bitfield.
    self->offset = *poffset - (*pfield_size) / 8;
    if(is_bitfield) {
        assert(dict->size == dict->align);
        assert(0 <= (*pfield_size + *pbitofs));
        assert((*pfield_size + *pbitofs) < dict->size * 8);
        self->size = BUILD_SIZE(bitsize, *pfield_size + *pbitofs);
    } else {
        self->size = dict->size;
    }
    assert(*pfield_size + *pbitofs <= dict->size * 8);

    *pbitofs += bitsize;
    *psize = *poffset;
    *palign = align;

    assert(!is_bitfield || (LOW_BIT(self->size) <= self->size * 8));
}

PyObject *
PyCField_FromDesc(PyObject *desc, Py_ssize_t index,
                Py_ssize_t *pfield_size, int bitsize, Py_ssize_t *pbitofs,
                Py_ssize_t *psize, Py_ssize_t *poffset, Py_ssize_t *palign,
                int pack, int big_endian, int ms_struct)
{
    CFieldObject* self = (CFieldObject *)_PyObject_CallNoArgs((PyObject *)&PyCField_Type);
    if (self == NULL)
        return NULL;
    StgDictObject* dict = PyType_stgdict(desc);
    if (!dict) {
        PyErr_SetString(PyExc_TypeError,
                        "has no _stginfo_");
        Py_DECREF(self);
        return NULL;
    }

    PyObject* proto = desc;

    /*  Field descriptors for 'c_char * n' are be scpecial cased to
        return a Python string instead of an Array object instance...
    */
    SETFUNC setfunc = NULL;
    GETFUNC getfunc = NULL;
    if (PyCArrayTypeObject_Check(proto)) {
        StgDictObject *adict = PyType_stgdict(proto);
        StgDictObject *idict;
        if (adict && adict->proto) {
            idict = PyType_stgdict(adict->proto);
            if (!idict) {
                PyErr_SetString(PyExc_TypeError,
                                "has no _stginfo_");
                Py_DECREF(self);
                return NULL;
            }
            if (idict->getfunc == _ctypes_get_fielddesc("c")->getfunc) {
                struct fielddesc *fd = _ctypes_get_fielddesc("s");
                getfunc = fd->getfunc;
                setfunc = fd->setfunc;
            }
            if (idict->getfunc == _ctypes_get_fielddesc("u")->getfunc) {
                struct fielddesc *fd = _ctypes_get_fielddesc("U");
                getfunc = fd->getfunc;
                setfunc = fd->setfunc;
            }
        }
    }

    self->setfunc = setfunc;
    self->getfunc = getfunc;
    self->index = index;

    Py_INCREF(proto);
    self->proto = proto;

    int is_bitfield = !!bitsize;
    if(!is_bitfield) {
        bitsize = 8 * dict->size; // might still be 0 afterwards.
    }

    if (ms_struct || pack != 0) {
        PyCField_FromDesc_windows(desc, index,
                pfield_size, bitsize, pbitofs,
                psize, poffset, palign,
                pack, big_endian,
                self, dict,
                is_bitfield
                );
    } else {
        PyCField_FromDesc_linux(desc, index,
                pfield_size, bitsize, pbitofs,
                psize, poffset, palign,
                pack, big_endian,
                self, dict,
                is_bitfield
                );
    }

    if(big_endian && is_bitfield) {
        self->size = BUILD_SIZE(NUM_BITS(self->size), 8*dict->size - LOW_BIT(self->size) - bitsize);
    }
    return (PyObject *)self;
}

static int
PyCField_set(CFieldObject *self, PyObject *inst, PyObject *value)
{
    CDataObject *dst;
    char *ptr;
    if (!CDataObject_Check(inst)) {
        PyErr_SetString(PyExc_TypeError,
                        "not a ctype instance");
        return -1;
    }
    dst = (CDataObject *)inst;
    ptr = dst->b_ptr + self->offset;
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError,
                        "can't delete attribute");
        return -1;
    }
    return PyCData_set(inst, self->proto, self->setfunc, value,
                     self->index, self->size, ptr);
}

static PyObject *
PyCField_get(CFieldObject *self, PyObject *inst, PyTypeObject *type)
{
    CDataObject *src;
    if (inst == NULL) {
        Py_INCREF(self);
        return (PyObject *)self;
    }
    if (!CDataObject_Check(inst)) {
        PyErr_SetString(PyExc_TypeError,
                        "not a ctype instance");
        return NULL;
    }
    src = (CDataObject *)inst;
    return PyCData_get(self->proto, self->getfunc, inst,
                     self->index, self->size, src->b_ptr + self->offset);
}

static PyObject *
PyCField_get_offset(PyObject *self, void *data)
{
    return PyLong_FromSsize_t(((CFieldObject *)self)->offset);
}

static PyObject *
PyCField_get_size(PyObject *self, void *data)
{
    return PyLong_FromSsize_t(((CFieldObject *)self)->size);
}

static PyGetSetDef PyCField_getset[] = {
    { "offset", PyCField_get_offset, NULL, "offset in bytes of this field" },
    { "size", PyCField_get_size, NULL, "size in bytes of this field" },
    { NULL, NULL, NULL, NULL },
};

static int
PyCField_traverse(CFieldObject *self, visitproc visit, void *arg)
{
    Py_VISIT(self->proto);
    return 0;
}

static int
PyCField_clear(CFieldObject *self)
{
    Py_CLEAR(self->proto);
    return 0;
}

static void
PyCField_dealloc(PyObject *self)
{
    PyObject_GC_UnTrack(self);
    PyCField_clear((CFieldObject *)self);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
PyCField_repr(CFieldObject *self)
{
    PyObject *result;
    // TODO: use function.
    Py_ssize_t bits = NUM_BITS(self->size);
    Py_ssize_t size = LOW_BIT(self->size);
    const char *name;

    name = ((PyTypeObject *)self->proto)->tp_name;

    if (bits)
        result = PyUnicode_FromFormat(
            "<Field type=%s, ofs=%zd:%zd, bits=%zd>",
            name, self->offset, size, bits);
    else
        result = PyUnicode_FromFormat(
            "<Field type=%s, ofs=%zd, size=%zd>",
            name, self->offset, size);
    return result;
}

PyTypeObject PyCField_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_ctypes.CField",                                   /* tp_name */
    sizeof(CFieldObject),                       /* tp_basicsize */
    0,                                          /* tp_itemsize */
    PyCField_dealloc,                                   /* tp_dealloc */
    0,                                          /* tp_vectorcall_offset */
    0,                                          /* tp_getattr */
    0,                                          /* tp_setattr */
    0,                                          /* tp_as_async */
    (reprfunc)PyCField_repr,                            /* tp_repr */
    0,                                          /* tp_as_number */
    0,                                          /* tp_as_sequence */
    0,                                          /* tp_as_mapping */
    0,                                          /* tp_hash */
    0,                                          /* tp_call */
    0,                                          /* tp_str */
    0,                                          /* tp_getattro */
    0,                                          /* tp_setattro */
    0,                                          /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC, /* tp_flags */
    PyDoc_STR("Structure/Union member"),        /* tp_doc */
    (traverseproc)PyCField_traverse,                    /* tp_traverse */
    (inquiry)PyCField_clear,                            /* tp_clear */
    0,                                          /* tp_richcompare */
    0,                                          /* tp_weaklistoffset */
    0,                                          /* tp_iter */
    0,                                          /* tp_iternext */
    0,                                          /* tp_methods */
    0,                                          /* tp_members */
    PyCField_getset,                                    /* tp_getset */
    0,                                          /* tp_base */
    0,                                          /* tp_dict */
    (descrgetfunc)PyCField_get,                 /* tp_descr_get */
    (descrsetfunc)PyCField_set,                 /* tp_descr_set */
    0,                                          /* tp_dictoffset */
    0,                                          /* tp_init */
    0,                                          /* tp_alloc */
    PyCField_new,                               /* tp_new */
    0,                                          /* tp_free */
};


/******************************************************************/
/*
  Accessor functions
*/

/* Derived from Modules/structmodule.c:
   Helper routine to get a Python integer and raise the appropriate error
   if it isn't one */

static int
get_long(PyObject *v, long *p)
{
    long x = PyLong_AsUnsignedLongMask(v);
    if (x == -1 && PyErr_Occurred())
        return -1;
    *p = x;
    return 0;
}

/* Same, but handling unsigned long */

static int
get_ulong(PyObject *v, unsigned long *p)
{
    unsigned long x = PyLong_AsUnsignedLongMask(v);
    if (x == (unsigned long)-1 && PyErr_Occurred())
        return -1;
    *p = x;
    return 0;
}

/* Same, but handling native long long. */

static int
get_longlong(PyObject *v, long long *p)
{
    long long x = PyLong_AsUnsignedLongLongMask(v);
    if (x == -1 && PyErr_Occurred())
        return -1;
    *p = x;
    return 0;
}

/* Same, but handling native unsigned long long. */

static int
get_ulonglong(PyObject *v, unsigned long long *p)
{
    unsigned long long x = PyLong_AsUnsignedLongLongMask(v);
    if (x == (unsigned long long)-1 && PyErr_Occurred())
        return -1;
    *p = x;
    return 0;
}

/*****************************************************************
 * Integer fields, with bitfield support
 */

/* how to decode the size field, for integer get/set functions */
static inline
Py_ssize_t LOW_BIT(Py_ssize_t offset) {
    return offset & 0xFFFF;
}
static inline
Py_ssize_t NUM_BITS(Py_ssize_t bitsize) {
    return bitsize >> 16;
}

static inline
Py_ssize_t BUILD_SIZE(Py_ssize_t bitsize, Py_ssize_t offset) {
    assert(0 <= offset);
    assert(offset <= 0xFFFF);
    // We don't support zero length bitfields.
    // And GET_BITFIELD uses NUM_BITS(size)==0,
    // to figure out whether we are handling a bitfield.
    assert(0 < bitsize);
    Py_ssize_t result = (bitsize << 16) + offset;
    assert(bitsize == NUM_BITS(result));
    assert(offset == LOW_BIT(result));
    return result;
}

/* Doesn't work if NUM_BITS(size) == 0, but it never happens in SET() call. */
#define BIT_MASK(type, size) (((((type)1 << (NUM_BITS(size) - 1)) - 1) << 1) + 1)

/* This macro CHANGES the first parameter IN PLACE. For proper sign handling,
   we must first shift left, then right.
*/
#define GET_BITFIELD(v, size)                                           \
    if (NUM_BITS(size)) {                                               \
        v <<= (sizeof(v)*8 - LOW_BIT(size) - NUM_BITS(size));           \
        v >>= (sizeof(v)*8 - NUM_BITS(size));                           \
    }

/* This macro RETURNS the first parameter with the bit field CHANGED. */
#define SET(type, x, v, size)                                                 \
    (NUM_BITS(size) ?                                                   \
     ( ( (type)x & ~(BIT_MASK(type, size) << LOW_BIT(size)) ) | ( ((type)v & BIT_MASK(type, size)) << LOW_BIT(size) ) ) \
     : (type)v)

#if SIZEOF_SHORT == 2
#  define SWAP_SHORT _Py_bswap16
#else
#  error "unsupported short size"
#endif

#if SIZEOF_INT == 4
#  define SWAP_INT _Py_bswap32
#else
#  error "unsupported int size"
#endif

#if SIZEOF_LONG == 4
#  define SWAP_LONG _Py_bswap32
#elif SIZEOF_LONG == 8
#  define SWAP_LONG _Py_bswap64
#else
#  error "unsupported long size"
#endif

#if SIZEOF_LONG_LONG == 8
#  define SWAP_LONG_LONG _Py_bswap64
#else
#  error "unsupported long long size"
#endif

/*****************************************************************
 * The setter methods return an object which must be kept alive, to keep the
 * data valid which has been stored in the memory block.  The ctypes object
 * instance inserts this object into its 'b_objects' list.
 *
 * For simple Python types like integers or characters, there is nothing that
 * has to been kept alive, so Py_None is returned in these cases.  But this
 * makes inspecting the 'b_objects' list, which is accessible from Python for
 * debugging, less useful.
 *
 * So, defining the _CTYPES_DEBUG_KEEP symbol returns the original value
 * instead of Py_None.
 */

#ifdef _CTYPES_DEBUG_KEEP
#define _RET(x) Py_INCREF(x); return x
#else
#define _RET(X) Py_RETURN_NONE
#endif

/*****************************************************************
 * integer accessor methods, supporting bit fields
 */

static PyObject *
b_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    long val;
    if (get_long(value, &val) < 0)
        return NULL;
    *(signed char *)ptr = SET(signed char, *(signed char *)ptr, val, size);
    _RET(value);
}


static PyObject *
b_get(void *ptr, Py_ssize_t size)
{
    signed char val = *(signed char *)ptr;
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

static PyObject *
B_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long val;
    if (get_ulong(value, &val) < 0)
        return NULL;
    *(unsigned char *)ptr = SET(unsigned char, *(unsigned char*)ptr, val, size);
    _RET(value);
}


static PyObject *
B_get(void *ptr, Py_ssize_t size)
{
    unsigned char val = *(unsigned char *)ptr;
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

static PyObject *
h_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    long val;
    short x;
    if (get_long(value, &val) < 0)
        return NULL;
    memcpy(&x, ptr, sizeof(x));
    x = SET(short, x, val, size);
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}


static PyObject *
h_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    long val;
    short field;
    if (get_long(value, &val) < 0) {
        return NULL;
    }
    memcpy(&field, ptr, sizeof(field));
    field = SWAP_SHORT(field);
    field = SET(short, field, val, size);
    field = SWAP_SHORT(field);
    memcpy(ptr, &field, sizeof(field));
    _RET(value);
}

static PyObject *
h_get(void *ptr, Py_ssize_t size)
{
    short val;
    memcpy(&val, ptr, sizeof(val));
    GET_BITFIELD(val, size);
    return PyLong_FromLong((long)val);
}

static PyObject *
h_get_sw(void *ptr, Py_ssize_t size)
{
    short val;
    memcpy(&val, ptr, sizeof(val));
    val = SWAP_SHORT(val);
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

static PyObject *
H_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long val;
    unsigned short x;
    if (get_ulong(value, &val) < 0)
        return NULL;
    memcpy(&x, ptr, sizeof(x));
    x = SET(unsigned short, x, val, size);
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}

static PyObject *
H_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long val;
    unsigned short field;
    if (get_ulong(value, &val) < 0) {
        return NULL;
    }
    memcpy(&field, ptr, sizeof(field));
    field = SWAP_SHORT(field);
    field = SET(unsigned short, field, val, size);
    field = SWAP_SHORT(field);
    memcpy(ptr, &field, sizeof(field));
    _RET(value);
}


static PyObject *
H_get(void *ptr, Py_ssize_t size)
{
    unsigned short val;
    memcpy(&val, ptr, sizeof(val));
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

static PyObject *
H_get_sw(void *ptr, Py_ssize_t size)
{
    unsigned short val;
    memcpy(&val, ptr, sizeof(val));
    val = SWAP_SHORT(val);
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

static PyObject *
i_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    long val;
    int x;
    if (get_long(value, &val) < 0)
        return NULL;
    memcpy(&x, ptr, sizeof(x));
    x = SET(int, x, val, size);
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}

static PyObject *
i_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    long val;
    int field;
    if (get_long(value, &val) < 0) {
        return NULL;
    }
    memcpy(&field, ptr, sizeof(field));
    field = SWAP_INT(field);
    field = SET(int, field, val, size);
    field = SWAP_INT(field);
    memcpy(ptr, &field, sizeof(field));
    _RET(value);
}


static PyObject *
i_get(void *ptr, Py_ssize_t size)
{
    int val;
    memcpy(&val, ptr, sizeof(val));
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

static PyObject *
i_get_sw(void *ptr, Py_ssize_t size)
{
    int val;
    memcpy(&val, ptr, sizeof(val));
    val = SWAP_INT(val);
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

#ifndef MS_WIN32
/* http://msdn.microsoft.com/en-us/library/cc237864.aspx */
#define VARIANT_FALSE 0x0000
#define VARIANT_TRUE 0xFFFF
#endif
/* short BOOL - VARIANT_BOOL */
static PyObject *
vBOOL_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    switch (PyObject_IsTrue(value)) {
    case -1:
        return NULL;
    case 0:
        *(short int *)ptr = VARIANT_FALSE;
        _RET(value);
    default:
        *(short int *)ptr = VARIANT_TRUE;
        _RET(value);
    }
}

static PyObject *
vBOOL_get(void *ptr, Py_ssize_t size)
{
    return PyBool_FromLong((long)*(short int *)ptr);
}

static PyObject *
bool_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    switch (PyObject_IsTrue(value)) {
    case -1:
        return NULL;
    case 0:
        *(_Bool *)ptr = 0;
        _RET(value);
    default:
        *(_Bool *)ptr = 1;
        _RET(value);
    }
}

static PyObject *
bool_get(void *ptr, Py_ssize_t size)
{
    return PyBool_FromLong((long)*(_Bool *)ptr);
}

static PyObject *
I_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long val;
    unsigned int x;
    if (get_ulong(value, &val) < 0)
        return  NULL;
    memcpy(&x, ptr, sizeof(x));
    x = SET(unsigned int, x, val, size);
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}

static PyObject *
I_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long val;
    unsigned int field;
    if (get_ulong(value, &val) < 0) {
        return  NULL;
    }
    memcpy(&field, ptr, sizeof(field));
    field = SWAP_INT(field);
    field = SET(unsigned int, field, (unsigned int)val, size);
    field = SWAP_INT(field);
    memcpy(ptr, &field, sizeof(field));
    _RET(value);
}


static PyObject *
I_get(void *ptr, Py_ssize_t size)
{
    unsigned int val;
    memcpy(&val, ptr, sizeof(val));
    GET_BITFIELD(val, size);
    return PyLong_FromUnsignedLong(val);
}

static PyObject *
I_get_sw(void *ptr, Py_ssize_t size)
{
    unsigned int val;
    memcpy(&val, ptr, sizeof(val));
    val = SWAP_INT(val);
    GET_BITFIELD(val, size);
    return PyLong_FromUnsignedLong(val);
}

static PyObject *
l_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    long val;
    long x;
    if (get_long(value, &val) < 0)
        return NULL;
    memcpy(&x, ptr, sizeof(x));
    x = SET(long, x, val, size);
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}

static PyObject *
l_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    long val;
    long field;
    if (get_long(value, &val) < 0) {
        return NULL;
    }
    memcpy(&field, ptr, sizeof(field));
    field = SWAP_LONG(field);
    field = SET(long, field, val, size);
    field = SWAP_LONG(field);
    memcpy(ptr, &field, sizeof(field));
    _RET(value);
}


static PyObject *
l_get(void *ptr, Py_ssize_t size)
{
    long val;
    memcpy(&val, ptr, sizeof(val));
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

static PyObject *
l_get_sw(void *ptr, Py_ssize_t size)
{
    long val;
    memcpy(&val, ptr, sizeof(val));
    val = SWAP_LONG(val);
    GET_BITFIELD(val, size);
    return PyLong_FromLong(val);
}

static PyObject *
L_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long val;
    unsigned long x;
    if (get_ulong(value, &val) < 0)
        return  NULL;
    memcpy(&x, ptr, sizeof(x));
    x = SET(unsigned long, x, val, size);
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}

static PyObject *
L_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long val;
    unsigned long field;
    if (get_ulong(value, &val) < 0) {
        return  NULL;
    }
    memcpy(&field, ptr, sizeof(field));
    field = SWAP_LONG(field);
    field = SET(unsigned long, field, val, size);
    field = SWAP_LONG(field);
    memcpy(ptr, &field, sizeof(field));
    _RET(value);
}


static PyObject *
L_get(void *ptr, Py_ssize_t size)
{
    unsigned long val;
    memcpy(&val, ptr, sizeof(val));
    GET_BITFIELD(val, size);
    return PyLong_FromUnsignedLong(val);
}

static PyObject *
L_get_sw(void *ptr, Py_ssize_t size)
{
    unsigned long val;
    memcpy(&val, ptr, sizeof(val));
    val = SWAP_LONG(val);
    GET_BITFIELD(val, size);
    return PyLong_FromUnsignedLong(val);
}

static PyObject *
q_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    long long val;
    long long x;
    if (get_longlong(value, &val) < 0)
        return NULL;
    memcpy(&x, ptr, sizeof(x));
    x = SET(long long, x, val, size);
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}

static PyObject *
q_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    long long val;
    long long field;
    if (get_longlong(value, &val) < 0) {
        return NULL;
    }
    memcpy(&field, ptr, sizeof(field));
    field = SWAP_LONG_LONG(field);
    field = SET(long long, field, val, size);
    field = SWAP_LONG_LONG(field);
    memcpy(ptr, &field, sizeof(field));
    _RET(value);
}

static PyObject *
q_get(void *ptr, Py_ssize_t size)
{
    long long val;
    memcpy(&val, ptr, sizeof(val));
    GET_BITFIELD(val, size);
    return PyLong_FromLongLong(val);
}

static PyObject *
q_get_sw(void *ptr, Py_ssize_t size)
{
    long long val;
    memcpy(&val, ptr, sizeof(val));
    val = SWAP_LONG_LONG(val);
    GET_BITFIELD(val, size);
    return PyLong_FromLongLong(val);
}

static PyObject *
Q_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long long val;
    unsigned long long x;
    if (get_ulonglong(value, &val) < 0)
        return NULL;
    memcpy(&x, ptr, sizeof(x));
    x = SET(long long, x, val, size);
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}

static PyObject *
Q_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    unsigned long long val;
    unsigned long long field;
    if (get_ulonglong(value, &val) < 0) {
        return NULL;
    }
    memcpy(&field, ptr, sizeof(field));
    field = SWAP_LONG_LONG(field);
    field = SET(unsigned long long, field, val, size);
    field = SWAP_LONG_LONG(field);
    memcpy(ptr, &field, sizeof(field));
    _RET(value);
}

static PyObject *
Q_get(void *ptr, Py_ssize_t size)
{
    unsigned long long val;
    memcpy(&val, ptr, sizeof(val));
    GET_BITFIELD(val, size);
    return PyLong_FromUnsignedLongLong(val);
}

static PyObject *
Q_get_sw(void *ptr, Py_ssize_t size)
{
    unsigned long long val;
    memcpy(&val, ptr, sizeof(val));
    val = SWAP_LONG_LONG(val);
    GET_BITFIELD(val, size);
    return PyLong_FromUnsignedLongLong(val);
}

/*****************************************************************
 * non-integer accessor methods, not supporting bit fields
 */


static PyObject *
g_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    long double x;

    x = PyFloat_AsDouble(value);
    if (x == -1 && PyErr_Occurred())
        return NULL;
    memcpy(ptr, &x, sizeof(long double));
    _RET(value);
}

static PyObject *
g_get(void *ptr, Py_ssize_t size)
{
    long double val;
    memcpy(&val, ptr, sizeof(long double));
    return PyFloat_FromDouble(val);
}

static PyObject *
d_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    double x;

    x = PyFloat_AsDouble(value);
    if (x == -1 && PyErr_Occurred())
        return NULL;
    memcpy(ptr, &x, sizeof(double));
    _RET(value);
}

static PyObject *
d_get(void *ptr, Py_ssize_t size)
{
    double val;
    memcpy(&val, ptr, sizeof(val));
    return PyFloat_FromDouble(val);
}

static PyObject *
d_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    double x;

    x = PyFloat_AsDouble(value);
    if (x == -1 && PyErr_Occurred())
        return NULL;
#ifdef WORDS_BIGENDIAN
    if (PyFloat_Pack8(x, ptr, 1))
        return NULL;
#else
    if (PyFloat_Pack8(x, ptr, 0))
        return NULL;
#endif
    _RET(value);
}

static PyObject *
d_get_sw(void *ptr, Py_ssize_t size)
{
#ifdef WORDS_BIGENDIAN
    return PyFloat_FromDouble(PyFloat_Unpack8(ptr, 1));
#else
    return PyFloat_FromDouble(PyFloat_Unpack8(ptr, 0));
#endif
}

static PyObject *
f_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    float x;

    x = (float)PyFloat_AsDouble(value);
    if (x == -1 && PyErr_Occurred())
        return NULL;
    memcpy(ptr, &x, sizeof(x));
    _RET(value);
}

static PyObject *
f_get(void *ptr, Py_ssize_t size)
{
    float val;
    memcpy(&val, ptr, sizeof(val));
    return PyFloat_FromDouble(val);
}

static PyObject *
f_set_sw(void *ptr, PyObject *value, Py_ssize_t size)
{
    float x;

    x = (float)PyFloat_AsDouble(value);
    if (x == -1 && PyErr_Occurred())
        return NULL;
#ifdef WORDS_BIGENDIAN
    if (PyFloat_Pack4(x, ptr, 1))
        return NULL;
#else
    if (PyFloat_Pack4(x, ptr, 0))
        return NULL;
#endif
    _RET(value);
}

static PyObject *
f_get_sw(void *ptr, Py_ssize_t size)
{
#ifdef WORDS_BIGENDIAN
    return PyFloat_FromDouble(PyFloat_Unpack4(ptr, 1));
#else
    return PyFloat_FromDouble(PyFloat_Unpack4(ptr, 0));
#endif
}

/*
  py_object refcounts:

  1. If we have a py_object instance, O_get must Py_INCREF the returned
  object, of course.  If O_get is called from a function result, no py_object
  instance is created - so callproc.c::GetResult has to call Py_DECREF.

  2. The memory block in py_object owns a refcount.  So, py_object must call
  Py_DECREF on destruction.  Maybe only when b_needsfree is non-zero.
*/
static PyObject *
O_get(void *ptr, Py_ssize_t size)
{
    PyObject *ob = *(PyObject **)ptr;
    if (ob == NULL) {
        if (!PyErr_Occurred())
            /* Set an error if not yet set */
            PyErr_SetString(PyExc_ValueError,
                            "PyObject is NULL");
        return NULL;
    }
    Py_INCREF(ob);
    return ob;
}

static PyObject *
O_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    /* Hm, does the memory block need it's own refcount or not? */
    *(PyObject **)ptr = value;
    Py_INCREF(value);
    return value;
}


static PyObject *
c_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    if (PyBytes_Check(value) && PyBytes_GET_SIZE(value) == 1) {
        *(char *)ptr = PyBytes_AS_STRING(value)[0];
        _RET(value);
    }
    if (PyByteArray_Check(value) && PyByteArray_GET_SIZE(value) == 1) {
        *(char *)ptr = PyByteArray_AS_STRING(value)[0];
        _RET(value);
    }
    if (PyLong_Check(value))
    {
        long longval = PyLong_AsLong(value);
        if (longval < 0 || longval >= 256)
            goto error;
        *(char *)ptr = (char)longval;
        _RET(value);
    }
  error:
    PyErr_Format(PyExc_TypeError,
                 "one character bytes, bytearray or integer expected");
    return NULL;
}


static PyObject *
c_get(void *ptr, Py_ssize_t size)
{
    return PyBytes_FromStringAndSize((char *)ptr, 1);
}

/* u - a single wchar_t character */
static PyObject *
u_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    Py_ssize_t len;
    wchar_t chars[2];
    if (!PyUnicode_Check(value)) {
        PyErr_Format(PyExc_TypeError,
                        "unicode string expected instead of %s instance",
                        Py_TYPE(value)->tp_name);
        return NULL;
    } else
        Py_INCREF(value);

    len = PyUnicode_AsWideChar(value, chars, 2);
    if (len != 1) {
        Py_DECREF(value);
        PyErr_SetString(PyExc_TypeError,
                        "one character unicode string expected");
        return NULL;
    }

    *(wchar_t *)ptr = chars[0];
    Py_DECREF(value);

    _RET(value);
}


static PyObject *
u_get(void *ptr, Py_ssize_t size)
{
    return PyUnicode_FromWideChar((wchar_t *)ptr, 1);
}

/* U - a unicode string */
static PyObject *
U_get(void *ptr, Py_ssize_t size)
{
    Py_ssize_t len;
    wchar_t *p;

    size /= sizeof(wchar_t); /* we count character units here, not bytes */

    /* We need 'result' to be able to count the characters with wcslen,
       since ptr may not be NUL terminated.  If the length is smaller (if
       it was actually NUL terminated, we construct a new one and throw
       away the result.
    */
    /* chop off at the first NUL character, if any. */
    p = (wchar_t*)ptr;
    for (len = 0; len < size; ++len) {
        if (!p[len])
            break;
    }

    return PyUnicode_FromWideChar((wchar_t *)ptr, len);
}

static PyObject *
U_set(void *ptr, PyObject *value, Py_ssize_t length)
{
    /* It's easier to calculate in characters than in bytes */
    length /= sizeof(wchar_t);

    if (!PyUnicode_Check(value)) {
        PyErr_Format(PyExc_TypeError,
                        "unicode string expected instead of %s instance",
                        Py_TYPE(value)->tp_name);
        return NULL;
    }

    Py_ssize_t size = PyUnicode_AsWideChar(value, NULL, 0);
    if (size < 0) {
        return NULL;
    }
    // PyUnicode_AsWideChar() returns number of wchars including trailing null byte,
    // when it is called with NULL.
    size--;
    assert(size >= 0);
    if (size > length) {
        PyErr_Format(PyExc_ValueError,
                     "string too long (%zd, maximum length %zd)",
                     size, length);
        return NULL;
    }
    if (PyUnicode_AsWideChar(value, (wchar_t *)ptr, length) == -1) {
        return NULL;
    }

    Py_INCREF(value);
    return value;
}


static PyObject *
s_get(void *ptr, Py_ssize_t size)
{
    Py_ssize_t i;
    char *p;

    p = (char *)ptr;
    for (i = 0; i < size; ++i) {
        if (*p++ == '\0')
            break;
    }

    return PyBytes_FromStringAndSize((char *)ptr, (Py_ssize_t)i);
}

static PyObject *
s_set(void *ptr, PyObject *value, Py_ssize_t length)
{
    const char *data;
    Py_ssize_t size;

    if(!PyBytes_Check(value)) {
        PyErr_Format(PyExc_TypeError,
                     "expected bytes, %s found",
                     Py_TYPE(value)->tp_name);
        return NULL;
    }

    data = PyBytes_AS_STRING(value);
    // bpo-39593: Use strlen() to truncate the string at the first null character.
    size = strlen(data);

    if (size < length) {
        /* This will copy the terminating NUL character
         * if there is space for it.
         */
        ++size;
    } else if (size > length) {
        PyErr_Format(PyExc_ValueError,
                     "bytes too long (%zd, maximum length %zd)",
                     size, length);
        return NULL;
    }
    /* Also copy the terminating NUL character if there is space */
    memcpy((char *)ptr, data, size);

    _RET(value);
}

static PyObject *
z_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    if (value == Py_None) {
        *(char **)ptr = NULL;
        Py_INCREF(value);
        return value;
    }
    if (PyBytes_Check(value)) {
        *(const char **)ptr = PyBytes_AsString(value);
        Py_INCREF(value);
        return value;
    } else if (PyLong_Check(value)) {
#if SIZEOF_VOID_P == SIZEOF_LONG_LONG
        *(char **)ptr = (char *)PyLong_AsUnsignedLongLongMask(value);
#else
        *(char **)ptr = (char *)PyLong_AsUnsignedLongMask(value);
#endif
        _RET(value);
    }
    PyErr_Format(PyExc_TypeError,
                 "bytes or integer address expected instead of %s instance",
                 Py_TYPE(value)->tp_name);
    return NULL;
}

static PyObject *
z_get(void *ptr, Py_ssize_t size)
{
    /* XXX What about invalid pointers ??? */
    if (*(void **)ptr) {
        return PyBytes_FromStringAndSize(*(char **)ptr,
                                         strlen(*(char **)ptr));
    } else {
        Py_RETURN_NONE;
    }
}

static PyObject *
Z_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    PyObject *keep;
    wchar_t *buffer;
    Py_ssize_t bsize;

    if (value == Py_None) {
        *(wchar_t **)ptr = NULL;
        Py_INCREF(value);
        return value;
    }
    if (PyLong_Check(value)) {
#if SIZEOF_VOID_P == SIZEOF_LONG_LONG
        *(wchar_t **)ptr = (wchar_t *)PyLong_AsUnsignedLongLongMask(value);
#else
        *(wchar_t **)ptr = (wchar_t *)PyLong_AsUnsignedLongMask(value);
#endif
        Py_RETURN_NONE;
    }
    if (!PyUnicode_Check(value)) {
        PyErr_Format(PyExc_TypeError,
                     "unicode string or integer address expected instead of %s instance",
                     Py_TYPE(value)->tp_name);
        return NULL;
    }

    /* We must create a wchar_t* buffer from the unicode object,
       and keep it alive */
    buffer = PyUnicode_AsWideCharString(value, &bsize);
    if (!buffer)
        return NULL;
    keep = PyCapsule_New(buffer, CTYPES_CFIELD_CAPSULE_NAME_PYMEM, pymem_destructor);
    if (!keep) {
        PyMem_Free(buffer);
        return NULL;
    }
    *(wchar_t **)ptr = buffer;
    return keep;
}

static PyObject *
Z_get(void *ptr, Py_ssize_t size)
{
    wchar_t *p;
    p = *(wchar_t **)ptr;
    if (p) {
        return PyUnicode_FromWideChar(p, wcslen(p));
    } else {
        Py_RETURN_NONE;
    }
}


#ifdef MS_WIN32
static PyObject *
BSTR_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    BSTR bstr;

    /* convert value into a PyUnicodeObject or NULL */
    if (Py_None == value) {
        value = NULL;
    } else if (!PyUnicode_Check(value)) {
        PyErr_Format(PyExc_TypeError,
                        "unicode string expected instead of %s instance",
                        Py_TYPE(value)->tp_name);
        return NULL;
    }

    /* create a BSTR from value */
    if (value) {
        Py_ssize_t wsize;
        wchar_t *wvalue = PyUnicode_AsWideCharString(value, &wsize);
        if (wvalue == NULL) {
            return NULL;
        }
        if ((unsigned) wsize != wsize) {
            PyErr_SetString(PyExc_ValueError, "String too long for BSTR");
            PyMem_Free(wvalue);
            return NULL;
        }
        bstr = SysAllocStringLen(wvalue, (unsigned)wsize);
        PyMem_Free(wvalue);
    } else
        bstr = NULL;

    /* free the previous contents, if any */
    if (*(BSTR *)ptr)
        SysFreeString(*(BSTR *)ptr);

    /* and store it */
    *(BSTR *)ptr = bstr;

    /* We don't need to keep any other object */
    _RET(value);
}


static PyObject *
BSTR_get(void *ptr, Py_ssize_t size)
{
    BSTR p;
    p = *(BSTR *)ptr;
    if (p)
        return PyUnicode_FromWideChar(p, SysStringLen(p));
    else {
        /* Hm, it seems NULL pointer and zero length string are the
           same in BSTR, see Don Box, p 81
        */
        Py_RETURN_NONE;
    }
}
#endif

static PyObject *
P_set(void *ptr, PyObject *value, Py_ssize_t size)
{
    void *v;
    if (value == Py_None) {
        *(void **)ptr = NULL;
        _RET(value);
    }

    if (!PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError,
                        "cannot be converted to pointer");
        return NULL;
    }

#if SIZEOF_VOID_P <= SIZEOF_LONG
    v = (void *)PyLong_AsUnsignedLongMask(value);
#else
#if SIZEOF_LONG_LONG < SIZEOF_VOID_P
#   error "PyLong_AsVoidPtr: sizeof(long long) < sizeof(void*)"
#endif
    v = (void *)PyLong_AsUnsignedLongLongMask(value);
#endif

    if (PyErr_Occurred())
        return NULL;

    *(void **)ptr = v;
    _RET(value);
}

static PyObject *
P_get(void *ptr, Py_ssize_t size)
{
    if (*(void **)ptr == NULL) {
        Py_RETURN_NONE;
    }
    return PyLong_FromVoidPtr(*(void **)ptr);
}

static struct fielddesc formattable[] = {
    { 's', s_set, s_get, NULL},
    { 'b', b_set, b_get, NULL},
    { 'B', B_set, B_get, NULL},
    { 'c', c_set, c_get, NULL},
    { 'd', d_set, d_get, NULL, d_set_sw, d_get_sw},
    { 'g', g_set, g_get, NULL},
    { 'f', f_set, f_get, NULL, f_set_sw, f_get_sw},
    { 'h', h_set, h_get, NULL, h_set_sw, h_get_sw},
    { 'H', H_set, H_get, NULL, H_set_sw, H_get_sw},
    { 'i', i_set, i_get, NULL, i_set_sw, i_get_sw},
    { 'I', I_set, I_get, NULL, I_set_sw, I_get_sw},
    { 'l', l_set, l_get, NULL, l_set_sw, l_get_sw},
    { 'L', L_set, L_get, NULL, L_set_sw, L_get_sw},
    { 'q', q_set, q_get, NULL, q_set_sw, q_get_sw},
    { 'Q', Q_set, Q_get, NULL, Q_set_sw, Q_get_sw},
    { 'P', P_set, P_get, NULL},
    { 'z', z_set, z_get, NULL},
    { 'u', u_set, u_get, NULL},
    { 'U', U_set, U_get, NULL},
    { 'Z', Z_set, Z_get, NULL},
#ifdef MS_WIN32
    { 'X', BSTR_set, BSTR_get, NULL},
#endif
    { 'v', vBOOL_set, vBOOL_get, NULL},
#if SIZEOF__BOOL == SIZEOF_INT
    { '?', bool_set, bool_get, NULL, I_set_sw, I_get_sw},
#elif SIZEOF__BOOL == SIZEOF_LONG
    { '?', bool_set, bool_get, NULL, L_set_sw, L_get_sw},
#elif SIZEOF__BOOL == SIZEOF_LONG_LONG
    { '?', bool_set, bool_get, NULL, Q_set_sw, Q_get_sw},
#else
    { '?', bool_set, bool_get, NULL},
#endif /* SIZEOF__BOOL */
    { 'O', O_set, O_get, NULL},
    { 0, NULL, NULL, NULL},
};

/*
  Ideas: Implement VARIANT in this table, using 'V' code.
  Use '?' as code for BOOL.
*/

/* Delayed initialization. Windows cannot statically reference dynamically
   loaded addresses from DLLs. */
void
_ctypes_init_fielddesc(void)
{
    struct fielddesc *fd = formattable;
    for (; fd->code; ++fd) {
        switch (fd->code) {
        case 's': fd->pffi_type = &ffi_type_pointer; break;
        case 'b': fd->pffi_type = &ffi_type_schar; break;
        case 'B': fd->pffi_type = &ffi_type_uchar; break;
        case 'c': fd->pffi_type = &ffi_type_schar; break;
        case 'd': fd->pffi_type = &ffi_type_double; break;
        case 'g': fd->pffi_type = &ffi_type_longdouble; break;
        case 'f': fd->pffi_type = &ffi_type_float; break;
        case 'h': fd->pffi_type = &ffi_type_sshort; break;
        case 'H': fd->pffi_type = &ffi_type_ushort; break;
        case 'i': fd->pffi_type = &ffi_type_sint; break;
        case 'I': fd->pffi_type = &ffi_type_uint; break;
        /* XXX Hm, sizeof(int) == sizeof(long) doesn't hold on every platform */
        /* As soon as we can get rid of the type codes, this is no longer a problem */
    #if SIZEOF_LONG == 4
        case 'l': fd->pffi_type = &ffi_type_sint32; break;
        case 'L': fd->pffi_type = &ffi_type_uint32; break;
    #elif SIZEOF_LONG == 8
        case 'l': fd->pffi_type = &ffi_type_sint64; break;
        case 'L': fd->pffi_type = &ffi_type_uint64; break;
    #else
        #error
    #endif
    #if SIZEOF_LONG_LONG == 8
        case 'q': fd->pffi_type = &ffi_type_sint64; break;
        case 'Q': fd->pffi_type = &ffi_type_uint64; break;
    #else
        #error
    #endif
        case 'P': fd->pffi_type = &ffi_type_pointer; break;
        case 'z': fd->pffi_type = &ffi_type_pointer; break;
        case 'u':
            if (sizeof(wchar_t) == sizeof(short))
                fd->pffi_type = &ffi_type_sshort;
            else if (sizeof(wchar_t) == sizeof(int))
                fd->pffi_type = &ffi_type_sint;
            else if (sizeof(wchar_t) == sizeof(long))
                fd->pffi_type = &ffi_type_slong;
            else
                Py_UNREACHABLE();
            break;
        case 'U': fd->pffi_type = &ffi_type_pointer; break;
        case 'Z': fd->pffi_type = &ffi_type_pointer; break;
    #ifdef MS_WIN32
        case 'X': fd->pffi_type = &ffi_type_pointer; break;
    #endif
        case 'v': fd->pffi_type = &ffi_type_sshort; break;
    #if SIZEOF__BOOL == 1
        case '?': fd->pffi_type = &ffi_type_uchar; break; /* Also fallback for no native _Bool support */
    #elif SIZEOF__BOOL == SIZEOF_SHORT
        case '?': fd->pffi_type = &ffi_type_ushort; break;
    #elif SIZEOF__BOOL == SIZEOF_INT
        case '?': fd->pffi_type = &ffi_type_uint; break;
    #elif SIZEOF__BOOL == SIZEOF_LONG
        case '?': fd->pffi_type = &ffi_type_ulong; break;
    #elif SIZEOF__BOOL == SIZEOF_LONG_LONG
        case '?': fd->pffi_type = &ffi_type_ulong; break;
    #endif /* SIZEOF__BOOL */
        case 'O': fd->pffi_type = &ffi_type_pointer; break;
        default:
            Py_UNREACHABLE();
        }
    }

}

struct fielddesc *
_ctypes_get_fielddesc(const char *fmt)
{
    static int initialized = 0;
    struct fielddesc *table = formattable;

    if (!initialized) {
        initialized = 1;
        _ctypes_init_fielddesc();
    }

    for (; table->code; ++table) {
        if (table->code == fmt[0])
            return table;
    }
    return NULL;
}

/*---------------- EOF ----------------*/
