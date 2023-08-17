// Auto-generated by Tools/build/generate_opcode_h.py from Lib/opcode.py

#ifndef Py_INTERNAL_OPCODE_H
#define Py_INTERNAL_OPCODE_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#include "opcode.h"

extern const uint8_t _PyOpcode_Caches[256];

#ifdef NEED_OPCODE_TABLES

const uint8_t _PyOpcode_Caches[256] = {
    [LOAD_GLOBAL] = 4,
    [BINARY_OP] = 1,
    [UNPACK_SEQUENCE] = 1,
    [COMPARE_OP] = 1,
    [BINARY_SUBSCR] = 1,
    [FOR_ITER] = 1,
    [LOAD_SUPER_ATTR] = 1,
    [LOAD_ATTR] = 9,
    [STORE_ATTR] = 4,
    [CALL] = 3,
    [STORE_SUBSCR] = 1,
    [SEND] = 1,
    [JUMP_BACKWARD] = 1,
    [TO_BOOL] = 3,
};
#endif   // NEED_OPCODE_TABLES

#ifdef __cplusplus
}
#endif
#endif  // !Py_INTERNAL_OPCODE_H
