#define Py_BUILD_CORE

#include "Python.h"

#include "pycore_frame.h"

// Stuff that will be patched at "JIT time":
extern int _justin_continue(PyThreadState *tstate, _PyInterpreterFrame *frame, PyObject **stack_pointer);
extern int _justin_stacklevel;

int
_justin_trampoline(void)
{
    int stacklevel = (uintptr_t)&_justin_stacklevel;
    PyThreadState *tstate = PyThreadState_GET();
    _PyInterpreterFrame *frame = tstate->cframe->current_frame;
    PyObject **stack_pointer = _PyFrame_Stackbase(frame) + stacklevel;
    return _justin_continue(tstate, frame, stack_pointer);
}