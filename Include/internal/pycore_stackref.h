#ifndef Py_INTERNAL_STACKREF_H
#define Py_INTERNAL_STACKREF_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#include "pycore_object_deferred.h"

#include <stddef.h>

typedef union {
    uintptr_t bits;
} _PyStackRef;


#define Py_TAG_DEFERRED (1)

// To catch where stackrefs leak out to the heap,
// in both current and future code.
#ifdef Py_DEBUG
#   define Py_TAG_PTR   (3)
#   define Py_TAG       (3)
#else
#   define Py_TAG_PTR   (0)
#   define Py_TAG       (1)
#endif

#ifdef Py_GIL_DISABLED
static const _PyStackRef Py_STACKREF_NULL = { .bits = 0 | Py_TAG_DEFERRED};
#else
static const _PyStackRef Py_STACKREF_NULL = { .bits = 0 };
#endif

static inline int
PyStackRef_IsNull(_PyStackRef stackref)
{
    return stackref.bits == Py_STACKREF_NULL.bits;
}

static inline int
PyStackRef_IsDeferred(_PyStackRef ref)
{
    return ((ref.bits & Py_TAG) == Py_TAG_DEFERRED);
}

// Gets a PyObject * from a _PyStackRef
static inline PyObject *
PyStackRef_AsPyObjectBorrow(_PyStackRef tagged)
{
#ifdef Py_GIL_DISABLED
    PyObject *cleared = ((PyObject *)((tagged).bits & (~Py_TAG)));
    return cleared;
#else
    assert((tagged.bits & Py_TAG) == 0);
    return (PyObject *)tagged.bits;
#endif
}

// Converts a PyObject * to a PyStackRef, stealing the reference
static inline _PyStackRef
_PyStackRef_FromPyObjectSteal(PyObject *obj)
{
#ifdef Py_GIL_DISABLED
    // Make sure we don't take an already tagged value.
    assert(((uintptr_t)obj & Py_TAG) == 0);
    int tag = (obj == NULL || _Py_IsImmortal(obj)) ? (Py_TAG_DEFERRED) : Py_TAG_PTR;
    return ((_PyStackRef){.bits = ((uintptr_t)(obj)) | tag});
#else
    // Make sure we don't take an already tagged value.
    assert(((uintptr_t)obj & Py_TAG) == 0);
    return ((_PyStackRef){.bits = ((uintptr_t)(obj))});
#endif
}
#define PyStackRef_FromPyObjectSteal(obj) _PyStackRef_FromPyObjectSteal(_PyObject_CAST(obj))

// Converts a PyObject * to a PyStackRef, with a new reference
static inline _PyStackRef
PyStackRef_FromPyObjectNew(PyObject *obj)
{
#ifdef Py_GIL_DISABLED
    // Make sure we don't take an already tagged value.
    assert(((uintptr_t)obj & Py_TAG) == 0);
    assert(obj != NULL);
    // TODO (gh-117139): Add deferred objects later.
    if (_Py_IsImmortal(obj)) {
        return (_PyStackRef){ .bits = (uintptr_t)obj | Py_TAG_DEFERRED };
    }
    else {
        return (_PyStackRef){ .bits = (uintptr_t)(Py_NewRef(obj)) | Py_TAG_PTR };
    }
#else
    return (_PyStackRef){ .bits = (uintptr_t)(Py_NewRef(obj)) };
#endif
}
#define PyStackRef_FromPyObjectNew(obj) PyStackRef_FromPyObjectNew(_PyObject_CAST(obj))


// Converts a PyStackRef back to a PyObject *, converting deferred references
// to new references.
static inline PyObject *
PyStackRef_AsPyObjectNew(_PyStackRef tagged)
{
#ifdef Py_GIL_DISABLED
    if (!PyStackRef_IsNull(tagged) && PyStackRef_IsDeferred(tagged)) {
        assert(_Py_IsImmortal(PyStackRef_AsPyObjectBorrow(tagged)));
        return Py_NewRef(PyStackRef_AsPyObjectBorrow(tagged));
    }
#endif
    return PyStackRef_AsPyObjectBorrow(tagged);
}

static inline void
_Py_untag_stack_borrowed(PyObject **dst, const _PyStackRef *src, size_t length)
{
    for (size_t i = 0; i < length; i++) {
        dst[i] = PyStackRef_AsPyObjectBorrow(src[i]);
    }
}

static inline void
_Py_untag_stack_steal(PyObject **dst, const _PyStackRef *src, size_t length)
{
    for (size_t i = 0; i < length; i++) {
        dst[i] = PyStackRef_AsPyObjectNew(src[i]);
    }
}

#define PyStackRef_SET(dst, src) \
    do { \
        _PyStackRef *_tmp_dst_ptr = &(dst); \
        _PyStackRef _tmp_old_dst = (*_tmp_dst_ptr); \
        *_tmp_dst_ptr = (src); \
        PyStackRef_CLOSE(_tmp_old_dst); \
    } while (0)

#define PyStackRef_CLEAR(op) \
    do { \
        _PyStackRef *_tmp_op_ptr = &(op); \
        _PyStackRef _tmp_old_op = (*_tmp_op_ptr); \
        if (!PyStackRef_IsNull(_tmp_old_op)) { \
            *_tmp_op_ptr = Py_STACKREF_NULL; \
            PyStackRef_CLOSE(_tmp_old_op); \
        } \
    } while (0)

static inline void
PyStackRef_CLOSE(_PyStackRef tagged)
{
#ifdef Py_GIL_DISABLED
    if (PyStackRef_IsDeferred(tagged)) {
        // No assert for being immortal or deferred here.
        // The GC unsets deferred objects right before clearing.
        return;
    }

    Py_DECREF(PyStackRef_AsPyObjectBorrow(tagged));
#else
    Py_XDECREF(PyStackRef_AsPyObjectBorrow(tagged));
#endif
}

static inline _PyStackRef
PyStackRef_DUP(_PyStackRef tagged)
{
#ifdef Py_GIL_DISABLED
    if (PyStackRef_IsDeferred(tagged)) {
        assert(PyStackRef_IsNull(tagged) ||
            _Py_IsImmortal(PyStackRef_AsPyObjectBorrow(tagged)));
        return tagged;
    }
    Py_INCREF(PyStackRef_AsPyObjectBorrow(tagged));
    return tagged;
#else
    Py_XINCREF(PyStackRef_AsPyObjectBorrow(tagged));
    return tagged;
#endif
}


#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_STACKREF_H */
