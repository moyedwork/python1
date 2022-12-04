/* Support for legacy tracing on top of PEP 669 instrumentation
 * Provides callables to forward PEP 669 events to legacy events.
 */

#include <stddef.h>
#include "Python.h"
#include "pycore_instruments.h"
#include "pycore_pyerrors.h"
#include "pycore_pymem.h"
#include "pycore_pystate.h"       // _PyInterpreterState_GET()
#include "pycore_sysmodule.h"

typedef struct _PyLegacyEventHandler {
    PyObject_HEAD
    vectorcallfunc vectorcall;
    int event;
} _PyLegacyEventHandler;

static void
dealloc(_PyLegacyEventHandler *self)
{
    PyObject_Free(self);
}


/* The Py_tracefunc function expects the following arguments:
 *   frame: FrameObject
 *   kind: c-int
 *   arg: The arg
 */

static PyObject *
call_profile_func(_PyLegacyEventHandler *self, PyObject *arg)
{
    PyThreadState *tstate = _PyThreadState_GET();
    if (tstate->c_profilefunc == NULL) {
        Py_RETURN_NONE;
    }
    if (tstate->tracing) {
        Py_RETURN_NONE;
    }
    PyFrameObject* frame = PyEval_GetFrame();
    Py_INCREF(frame);
    assert(frame != NULL);
    tstate->tracing++;
    int err = tstate->c_profilefunc(tstate->c_profileobj, frame, self->event, arg);
    tstate->tracing--;
    Py_DECREF(frame);
    if (err) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *
sys_profile_func2(
    _PyLegacyEventHandler *self, PyObject *const *args,
    size_t nargsf, PyObject *kwnames
) {
    assert(kwnames == NULL);
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
    assert(nargs == 2);
    return call_profile_func(self, Py_None);
}

static PyObject *
sys_profile_func3(
    _PyLegacyEventHandler *self, PyObject *const *args,
    size_t nargsf, PyObject *kwnames
) {
    assert(kwnames == NULL);
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
    assert(nargs == 3);
    return call_profile_func(self, args[2]);
}

static PyObject *
sys_profile_call_or_return(
    _PyLegacyEventHandler *self, PyObject *const *args,
    size_t nargsf, PyObject *kwnames
) {
    assert(kwnames == NULL);
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
    assert(nargs == 3);
    PyObject *callable = args[2];
    if (!PyCFunction_Check(callable) && Py_TYPE(callable) != &PyMethodDescr_Type) {
        Py_RETURN_NONE;
    }
    return call_profile_func(self, callable);
}

static PyObject *
sys_profile_exception_func(
    _PyLegacyEventHandler *self, PyObject *const *args,
    size_t nargsf, PyObject *kwnames
) {
    assert(kwnames == NULL);
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
    assert(nargs == 3);
    _PyErr_StackItem *err_info = _PyErr_GetTopmostException(_PyThreadState_GET());
    PyObject *arg = _PyErr_StackItemToExcInfoTuple(err_info);
    if (arg == NULL) {
        return NULL;
    }
    PyObject *res = call_profile_func(self, arg);
    Py_DECREF(arg);
    return res;
}

static PyObject *
sys_trace_none_func(
    _PyLegacyEventHandler *self, PyObject *const *args,
    size_t nargsf, PyObject *kwnames
) {
    assert(kwnames == NULL);
    Py_ssize_t nargs = PyVectorcall_NARGS(nargsf);
    assert(nargs == 3);
    return call_profile_func(self, Py_None);
}


PyTypeObject _PyLegacyEventHandler_Type = {

    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "sys.profile_event_handler",
    sizeof(_PyLegacyEventHandler),
    .tp_dealloc = (destructor)dealloc,
    .tp_vectorcall_offset = offsetof(_PyLegacyEventHandler, vectorcall),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_VECTORCALL,
    .tp_call = PyVectorcall_Call,
};

static int
set_callbacks(int tool, vectorcallfunc vectorcall, int legacy_event, int event1, int event2)
{
    _PyLegacyEventHandler *callback =
        PyObject_NEW(_PyLegacyEventHandler, &_PyLegacyEventHandler_Type);
    if (callback == NULL) {
        return -1;
    }
    callback->vectorcall = vectorcall;
    callback->event = legacy_event;
    Py_XDECREF(_PyMonitoring_RegisterCallback(tool, event1, (PyObject *)callback));
    if (event2 >= 0) {
        Py_XDECREF(_PyMonitoring_RegisterCallback(tool, event2, (PyObject *)callback));
    }
    Py_DECREF(callback);
    return 0;
}

#ifndef NDEBUG
/* Ensure that tstate is valid: sanity check for PyEval_AcquireThread() and
   PyEval_RestoreThread(). Detect if tstate memory was freed. It can happen
   when a thread continues to run after Python finalization, especially
   daemon threads. */
static int
is_tstate_valid(PyThreadState *tstate)
{
    assert(!_PyMem_IsPtrFreed(tstate));
    assert(!_PyMem_IsPtrFreed(tstate->interp));
    return 1;
}
#endif

int
_PyEval_SetProfile(PyThreadState *tstate, Py_tracefunc func, PyObject *arg)
{
    assert(is_tstate_valid(tstate));
    /* The caller must hold the GIL */
    assert(PyGILState_Check());

    /* Call _PySys_Audit() in the context of the current thread state,
       even if tstate is not the current thread state. */
    PyThreadState *current_tstate = _PyThreadState_GET();
    if (_PySys_Audit(current_tstate, "sys.setprofile", NULL) < 0) {
        return -1;
    }
    int delta = (func != NULL) - (tstate->c_profilefunc != NULL);
    tstate->c_profilefunc = func;
    PyObject *old_profileobj = tstate->c_profileobj;
    tstate->c_profileobj = Py_XNewRef(arg);
    /* Flag that tracing or profiling is turned on */
    _PyThreadState_UpdateTracingState(tstate);

    /* Setup PEP 669 monitoring callbacks and events. */
    tstate->interp->sys_profiling_threads += delta;
    assert(tstate->interp->sys_profiling_threads >= 0);
    if (!tstate->interp->sys_profile_initialized) {
        tstate->interp->sys_profile_initialized = true;
        if (set_callbacks(PY_INSTRUMENT_SYS_PROFILE,
            (vectorcallfunc)sys_profile_func2, PyTrace_CALL,
                        PY_MONITORING_EVENT_PY_START, PY_MONITORING_EVENT_PY_RESUME)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_PROFILE,
            (vectorcallfunc)sys_profile_func3, PyTrace_RETURN,
                        PY_MONITORING_EVENT_PY_RETURN, PY_MONITORING_EVENT_PY_YIELD)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_PROFILE,
            (vectorcallfunc)sys_profile_func2, PyTrace_RETURN,
                        PY_MONITORING_EVENT_PY_UNWIND, -1)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_PROFILE,
            (vectorcallfunc)sys_profile_call_or_return, PyTrace_C_CALL,
                        PY_MONITORING_EVENT_CALL, -1)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_PROFILE,
            (vectorcallfunc)sys_profile_call_or_return, PyTrace_C_RETURN,
                        PY_MONITORING_EVENT_C_RETURN, -1)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_PROFILE,
            (vectorcallfunc)sys_profile_call_or_return, PyTrace_C_EXCEPTION,
                        PY_MONITORING_EVENT_C_RAISE, -1)) {
            return -1;
        }
    }
    if (tstate->interp->sys_profiling_threads && delta) {
        uint32_t events =
            (1 << PY_MONITORING_EVENT_PY_START) | (1 << PY_MONITORING_EVENT_PY_RESUME) |
            (1 << PY_MONITORING_EVENT_PY_RETURN) | (1 << PY_MONITORING_EVENT_PY_YIELD) |
            (1 << PY_MONITORING_EVENT_CALL) | (1 << PY_MONITORING_EVENT_PY_UNWIND) |
            (1 << PY_MONITORING_EVENT_C_RETURN) | (1 << PY_MONITORING_EVENT_C_RAISE);
        _PyMonitoring_SetEvents(PY_INSTRUMENT_SYS_PROFILE, events);
    }
    else if (tstate->interp->sys_profiling_threads == 0) {
        _PyMonitoring_SetEvents(PY_INSTRUMENT_SYS_PROFILE, 0);
    }
    // gh-98257: Only call Py_XDECREF() once the new profile function is fully
    // set, so it's safe to call sys.setprofile() again (reentrant call).
    Py_XDECREF(old_profileobj);
    return 0;
}

int
_PyEval_SetTrace(PyThreadState *tstate, Py_tracefunc func, PyObject *arg)
{
    assert(is_tstate_valid(tstate));
    /* The caller must hold the GIL */
    assert(PyGILState_Check());

    /* Call _PySys_Audit() in the context of the current thread state,
       even if tstate is not the current thread state. */
    PyThreadState *current_tstate = _PyThreadState_GET();
    if (_PySys_Audit(current_tstate, "sys.settrace", NULL) < 0) {
        return -1;
    }

    int delta = (func != NULL) - (tstate->c_tracefunc != NULL);
    tstate->c_tracefunc = func;
    PyObject *old_traceobj = tstate->c_traceobj;
    tstate->c_traceobj = Py_XNewRef(arg);
    /* Flag that tracing or profiling is turned on */
    _PyThreadState_UpdateTracingState(tstate);

    /* Setup PEP 669 monitoring callbacks and events. */
    tstate->interp->sys_tracing_threads += delta;
    assert(tstate->interp->sys_tracing_threads >= 0);
    if (!tstate->interp->sys_trace_initialized) {
        tstate->interp->sys_trace_initialized = true;
        if (set_callbacks(PY_INSTRUMENT_SYS_TRACE,
            (vectorcallfunc)sys_profile_func2, PyTrace_CALL,
                        PY_MONITORING_EVENT_PY_START, PY_MONITORING_EVENT_PY_RESUME)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_TRACE,
            (vectorcallfunc)sys_profile_func3, PyTrace_RETURN,
                        PY_MONITORING_EVENT_PY_RETURN, PY_MONITORING_EVENT_PY_YIELD)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_TRACE,
            (vectorcallfunc)sys_profile_exception_func, PyTrace_EXCEPTION,
                        PY_MONITORING_EVENT_RAISE, -1)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_TRACE,
            (vectorcallfunc)sys_trace_none_func, PyTrace_LINE,
                        PY_MONITORING_EVENT_LINE, -1)) {
            return -1;
        }
        if (set_callbacks(PY_INSTRUMENT_SYS_TRACE,
            (vectorcallfunc)sys_trace_none_func, PyTrace_OPCODE,
                        PY_MONITORING_EVENT_INSTRUCTION, -1)) {
            return -1;
        }
    }
    if (tstate->interp->sys_tracing_threads) {
        uint32_t events =
            (1 << PY_MONITORING_EVENT_PY_START) | (1 << PY_MONITORING_EVENT_PY_RESUME) |
            (1 << PY_MONITORING_EVENT_PY_RETURN) | (1 << PY_MONITORING_EVENT_PY_YIELD) |
            (1 << PY_MONITORING_EVENT_RAISE) | (1 << PY_MONITORING_EVENT_LINE);
        if (tstate->interp->f_opcode_trace_set) {
            events |= (1 << PY_MONITORING_EVENT_INSTRUCTION);
        }
        _PyMonitoring_SetEvents(PY_INSTRUMENT_SYS_PROFILE, events);
    }
    else {
        _PyMonitoring_SetEvents(PY_INSTRUMENT_SYS_PROFILE, 0);
    }
    Py_XDECREF(old_traceobj);
    return 0;
}
