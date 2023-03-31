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

extern const uint8_t _PyOpcode_Deopt[256];

#ifdef NEED_OPCODE_TABLES
static const uint32_t _PyOpcode_RelativeJump[9] = {
    0U,
    0U,
    536870912U,
    135020544U,
    4163U,
    0U,
    0U,
    0U,
    48U,
};
static const uint32_t _PyOpcode_Jump[9] = {
    0U,
    0U,
    536870912U,
    135020544U,
    4163U,
    0U,
    0U,
    0U,
    48U,
};

const uint8_t _PyOpcode_Caches[256] = {
    [BINARY_SUBSCR] = 4,
    [STORE_SUBSCR] = 1,
    [UNPACK_SEQUENCE] = 1,
    [FOR_ITER] = 1,
    [STORE_ATTR] = 4,
    [LOAD_ATTR] = 9,
    [COMPARE_OP] = 1,
    [LOAD_GLOBAL] = 4,
    [BINARY_OP] = 1,
    [SEND] = 1,
    [CALL] = 4,
};

const uint8_t _PyOpcode_Deopt[256] = {
    [BB_TEST_ITER_GEN] = BB_TEST_ITER,
    [BB_TEST_ITER_LIST] = BB_TEST_ITER,
    [BB_TEST_ITER_RANGE] = BB_TEST_ITER,
    [BB_TEST_ITER_TUPLE] = BB_TEST_ITER,
    [BEFORE_ASYNC_WITH] = BEFORE_ASYNC_WITH,
    [BEFORE_WITH] = BEFORE_WITH,
    [BINARY_OP] = BINARY_OP,
    [BINARY_OP_ADD_FLOAT] = BINARY_OP,
    [BINARY_OP_ADD_INT] = BINARY_OP,
    [BINARY_OP_ADD_UNICODE] = BINARY_OP,
    [BINARY_OP_INPLACE_ADD_UNICODE] = BINARY_OP,
    [BINARY_OP_MULTIPLY_FLOAT] = BINARY_OP,
    [BINARY_OP_MULTIPLY_INT] = BINARY_OP,
    [BINARY_OP_SUBTRACT_FLOAT] = BINARY_OP,
    [BINARY_OP_SUBTRACT_INT] = BINARY_OP,
    [BINARY_SLICE] = BINARY_SLICE,
    [BINARY_SUBSCR] = BINARY_SUBSCR,
    [BINARY_SUBSCR_DICT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_GETITEM] = BINARY_SUBSCR,
    [BINARY_SUBSCR_LIST_INT] = BINARY_SUBSCR,
    [BINARY_SUBSCR_TUPLE_INT] = BINARY_SUBSCR,
    [BUILD_CONST_KEY_MAP] = BUILD_CONST_KEY_MAP,
    [BUILD_LIST] = BUILD_LIST,
    [BUILD_MAP] = BUILD_MAP,
    [BUILD_SET] = BUILD_SET,
    [BUILD_SLICE] = BUILD_SLICE,
    [BUILD_STRING] = BUILD_STRING,
    [BUILD_TUPLE] = BUILD_TUPLE,
    [CACHE] = CACHE,
    [CALL] = CALL,
    [CALL_BOUND_METHOD_EXACT_ARGS] = CALL,
    [CALL_BUILTIN_CLASS] = CALL,
    [CALL_BUILTIN_FAST_WITH_KEYWORDS] = CALL,
    [CALL_FUNCTION_EX] = CALL_FUNCTION_EX,
    [CALL_INTRINSIC_1] = CALL_INTRINSIC_1,
    [CALL_INTRINSIC_2] = CALL_INTRINSIC_2,
    [CALL_METHOD_DESCRIPTOR_FAST_WITH_KEYWORDS] = CALL,
    [CALL_NO_KW_BUILTIN_FAST] = CALL,
    [CALL_NO_KW_BUILTIN_O] = CALL,
    [CALL_NO_KW_ISINSTANCE] = CALL,
    [CALL_NO_KW_LEN] = CALL,
    [CALL_NO_KW_LIST_APPEND] = CALL,
    [CALL_NO_KW_METHOD_DESCRIPTOR_FAST] = CALL,
    [CALL_NO_KW_METHOD_DESCRIPTOR_NOARGS] = CALL,
    [CALL_NO_KW_METHOD_DESCRIPTOR_O] = CALL,
    [CALL_NO_KW_STR_1] = CALL,
    [CALL_NO_KW_TUPLE_1] = CALL,
    [CALL_NO_KW_TYPE_1] = CALL,
    [CALL_PY_EXACT_ARGS] = CALL,
    [CALL_PY_WITH_DEFAULTS] = CALL,
    [CHECK_EG_MATCH] = CHECK_EG_MATCH,
    [CHECK_EXC_MATCH] = CHECK_EXC_MATCH,
    [CLEANUP_THROW] = CLEANUP_THROW,
    [COMPARE_OP] = COMPARE_OP,
    [COMPARE_OP_FLOAT] = COMPARE_OP,
    [COMPARE_OP_INT] = COMPARE_OP,
    [COMPARE_OP_STR] = COMPARE_OP,
    [CONTAINS_OP] = CONTAINS_OP,
    [COPY] = COPY,
    [COPY_FREE_VARS] = COPY_FREE_VARS,
    [DELETE_ATTR] = DELETE_ATTR,
    [DELETE_DEREF] = DELETE_DEREF,
    [DELETE_FAST] = DELETE_FAST,
    [DELETE_GLOBAL] = DELETE_GLOBAL,
    [DELETE_NAME] = DELETE_NAME,
    [DELETE_SUBSCR] = DELETE_SUBSCR,
    [DICT_MERGE] = DICT_MERGE,
    [DICT_UPDATE] = DICT_UPDATE,
    [END_ASYNC_FOR] = END_ASYNC_FOR,
    [END_FOR] = END_FOR,
    [EXTENDED_ARG] = EXTENDED_ARG,
    [FORMAT_VALUE] = FORMAT_VALUE,
    [FOR_ITER] = FOR_ITER,
    [FOR_ITER_GEN] = FOR_ITER,
    [FOR_ITER_LIST] = FOR_ITER,
    [FOR_ITER_RANGE] = FOR_ITER,
    [FOR_ITER_TUPLE] = FOR_ITER,
    [GET_AITER] = GET_AITER,
    [GET_ANEXT] = GET_ANEXT,
    [GET_AWAITABLE] = GET_AWAITABLE,
    [GET_ITER] = GET_ITER,
    [GET_LEN] = GET_LEN,
    [GET_YIELD_FROM_ITER] = GET_YIELD_FROM_ITER,
    [IMPORT_FROM] = IMPORT_FROM,
    [IMPORT_NAME] = IMPORT_NAME,
    [INTERPRETER_EXIT] = INTERPRETER_EXIT,
    [IS_OP] = IS_OP,
    [JUMP_BACKWARD] = JUMP_BACKWARD,
    [JUMP_BACKWARD_NO_INTERRUPT] = JUMP_BACKWARD_NO_INTERRUPT,
    [JUMP_BACKWARD_QUICK] = JUMP_BACKWARD,
    [JUMP_FORWARD] = JUMP_FORWARD,
    [KW_NAMES] = KW_NAMES,
    [LIST_APPEND] = LIST_APPEND,
    [LIST_EXTEND] = LIST_EXTEND,
    [LOAD_ASSERTION_ERROR] = LOAD_ASSERTION_ERROR,
    [LOAD_ATTR] = LOAD_ATTR,
    [LOAD_ATTR_CLASS] = LOAD_ATTR,
    [LOAD_ATTR_GETATTRIBUTE_OVERRIDDEN] = LOAD_ATTR,
    [LOAD_ATTR_INSTANCE_VALUE] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_LAZY_DICT] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_NO_DICT] = LOAD_ATTR,
    [LOAD_ATTR_METHOD_WITH_VALUES] = LOAD_ATTR,
    [LOAD_ATTR_MODULE] = LOAD_ATTR,
    [LOAD_ATTR_PROPERTY] = LOAD_ATTR,
    [LOAD_ATTR_SLOT] = LOAD_ATTR,
    [LOAD_ATTR_WITH_HINT] = LOAD_ATTR,
    [LOAD_BUILD_CLASS] = LOAD_BUILD_CLASS,
    [LOAD_CLASSDEREF] = LOAD_CLASSDEREF,
    [LOAD_CLOSURE] = LOAD_CLOSURE,
    [LOAD_CONST] = LOAD_CONST,
    [LOAD_CONST__LOAD_FAST] = LOAD_CONST,
    [LOAD_DEREF] = LOAD_DEREF,
    [LOAD_FAST] = LOAD_FAST,
    [LOAD_FAST_CHECK] = LOAD_FAST_CHECK,
    [LOAD_FAST__LOAD_CONST] = LOAD_FAST,
    [LOAD_FAST__LOAD_FAST] = LOAD_FAST,
    [LOAD_GLOBAL] = LOAD_GLOBAL,
    [LOAD_GLOBAL_BUILTIN] = LOAD_GLOBAL,
    [LOAD_GLOBAL_MODULE] = LOAD_GLOBAL,
    [LOAD_NAME] = LOAD_NAME,
    [MAKE_CELL] = MAKE_CELL,
    [MAKE_FUNCTION] = MAKE_FUNCTION,
    [MAP_ADD] = MAP_ADD,
    [MATCH_CLASS] = MATCH_CLASS,
    [MATCH_KEYS] = MATCH_KEYS,
    [MATCH_MAPPING] = MATCH_MAPPING,
    [MATCH_SEQUENCE] = MATCH_SEQUENCE,
    [NOP] = NOP,
    [POP_EXCEPT] = POP_EXCEPT,
    [POP_JUMP_IF_FALSE] = POP_JUMP_IF_FALSE,
    [POP_JUMP_IF_NONE] = POP_JUMP_IF_NONE,
    [POP_JUMP_IF_NOT_NONE] = POP_JUMP_IF_NOT_NONE,
    [POP_JUMP_IF_TRUE] = POP_JUMP_IF_TRUE,
    [POP_TOP] = POP_TOP,
    [PUSH_EXC_INFO] = PUSH_EXC_INFO,
    [PUSH_NULL] = PUSH_NULL,
    [RAISE_VARARGS] = RAISE_VARARGS,
    [RERAISE] = RERAISE,
    [RESUME] = RESUME,
    [RESUME_QUICK] = RESUME,
    [RETURN_CONST] = RETURN_CONST,
    [RETURN_GENERATOR] = RETURN_GENERATOR,
    [RETURN_VALUE] = RETURN_VALUE,
    [SEND] = SEND,
    [SEND_GEN] = SEND,
    [SETUP_ANNOTATIONS] = SETUP_ANNOTATIONS,
    [SET_ADD] = SET_ADD,
    [SET_UPDATE] = SET_UPDATE,
    [STORE_ATTR] = STORE_ATTR,
    [STORE_ATTR_INSTANCE_VALUE] = STORE_ATTR,
    [STORE_ATTR_SLOT] = STORE_ATTR,
    [STORE_ATTR_WITH_HINT] = STORE_ATTR,
    [STORE_DEREF] = STORE_DEREF,
    [STORE_FAST] = STORE_FAST,
    [STORE_FAST__LOAD_FAST] = STORE_FAST,
    [STORE_FAST__STORE_FAST] = STORE_FAST,
    [STORE_GLOBAL] = STORE_GLOBAL,
    [STORE_NAME] = STORE_NAME,
    [STORE_SLICE] = STORE_SLICE,
    [STORE_SUBSCR] = STORE_SUBSCR,
    [STORE_SUBSCR_DICT] = STORE_SUBSCR,
    [STORE_SUBSCR_LIST_INT] = STORE_SUBSCR,
    [SWAP] = SWAP,
    [UNARY_INVERT] = UNARY_INVERT,
    [UNARY_NEGATIVE] = UNARY_NEGATIVE,
    [UNARY_NOT] = UNARY_NOT,
    [UNPACK_EX] = UNPACK_EX,
    [UNPACK_SEQUENCE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_LIST] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_TUPLE] = UNPACK_SEQUENCE,
    [UNPACK_SEQUENCE_TWO_TUPLE] = UNPACK_SEQUENCE,
    [WITH_EXCEPT_START] = WITH_EXCEPT_START,
    [YIELD_VALUE] = YIELD_VALUE,
};
#endif   // NEED_OPCODE_TABLES

#ifdef Py_DEBUG
static const char *const _PyOpcode_OpName[263] = {
    [CACHE] = "CACHE",
    [POP_TOP] = "POP_TOP",
    [PUSH_NULL] = "PUSH_NULL",
    [INTERPRETER_EXIT] = "INTERPRETER_EXIT",
    [END_FOR] = "END_FOR",
    [RESUME_QUICK] = "RESUME_QUICK",
    [JUMP_BACKWARD_QUICK] = "JUMP_BACKWARD_QUICK",
    [BINARY_OP_ADD_FLOAT] = "BINARY_OP_ADD_FLOAT",
    [BINARY_OP_ADD_INT] = "BINARY_OP_ADD_INT",
    [NOP] = "NOP",
    [BINARY_OP_ADD_UNICODE] = "BINARY_OP_ADD_UNICODE",
    [UNARY_NEGATIVE] = "UNARY_NEGATIVE",
    [UNARY_NOT] = "UNARY_NOT",
    [BINARY_OP_INPLACE_ADD_UNICODE] = "BINARY_OP_INPLACE_ADD_UNICODE",
    [BINARY_OP_MULTIPLY_FLOAT] = "BINARY_OP_MULTIPLY_FLOAT",
    [UNARY_INVERT] = "UNARY_INVERT",
    [BINARY_OP_MULTIPLY_INT] = "BINARY_OP_MULTIPLY_INT",
    [BINARY_OP_SUBTRACT_FLOAT] = "BINARY_OP_SUBTRACT_FLOAT",
    [BINARY_OP_SUBTRACT_INT] = "BINARY_OP_SUBTRACT_INT",
    [BINARY_SUBSCR_DICT] = "BINARY_SUBSCR_DICT",
    [BINARY_SUBSCR_GETITEM] = "BINARY_SUBSCR_GETITEM",
    [BINARY_SUBSCR_LIST_INT] = "BINARY_SUBSCR_LIST_INT",
    [BINARY_SUBSCR_TUPLE_INT] = "BINARY_SUBSCR_TUPLE_INT",
    [CALL_PY_EXACT_ARGS] = "CALL_PY_EXACT_ARGS",
    [CALL_PY_WITH_DEFAULTS] = "CALL_PY_WITH_DEFAULTS",
    [BINARY_SUBSCR] = "BINARY_SUBSCR",
    [BINARY_SLICE] = "BINARY_SLICE",
    [STORE_SLICE] = "STORE_SLICE",
    [CALL_BOUND_METHOD_EXACT_ARGS] = "CALL_BOUND_METHOD_EXACT_ARGS",
    [CALL_BUILTIN_CLASS] = "CALL_BUILTIN_CLASS",
    [GET_LEN] = "GET_LEN",
    [MATCH_MAPPING] = "MATCH_MAPPING",
    [MATCH_SEQUENCE] = "MATCH_SEQUENCE",
    [MATCH_KEYS] = "MATCH_KEYS",
    [CALL_BUILTIN_FAST_WITH_KEYWORDS] = "CALL_BUILTIN_FAST_WITH_KEYWORDS",
    [PUSH_EXC_INFO] = "PUSH_EXC_INFO",
    [CHECK_EXC_MATCH] = "CHECK_EXC_MATCH",
    [CHECK_EG_MATCH] = "CHECK_EG_MATCH",
    [CALL_METHOD_DESCRIPTOR_FAST_WITH_KEYWORDS] = "CALL_METHOD_DESCRIPTOR_FAST_WITH_KEYWORDS",
    [CALL_NO_KW_BUILTIN_FAST] = "CALL_NO_KW_BUILTIN_FAST",
    [CALL_NO_KW_BUILTIN_O] = "CALL_NO_KW_BUILTIN_O",
    [CALL_NO_KW_ISINSTANCE] = "CALL_NO_KW_ISINSTANCE",
    [CALL_NO_KW_LEN] = "CALL_NO_KW_LEN",
    [CALL_NO_KW_LIST_APPEND] = "CALL_NO_KW_LIST_APPEND",
    [CALL_NO_KW_METHOD_DESCRIPTOR_FAST] = "CALL_NO_KW_METHOD_DESCRIPTOR_FAST",
    [CALL_NO_KW_METHOD_DESCRIPTOR_NOARGS] = "CALL_NO_KW_METHOD_DESCRIPTOR_NOARGS",
    [CALL_NO_KW_METHOD_DESCRIPTOR_O] = "CALL_NO_KW_METHOD_DESCRIPTOR_O",
    [CALL_NO_KW_STR_1] = "CALL_NO_KW_STR_1",
    [CALL_NO_KW_TUPLE_1] = "CALL_NO_KW_TUPLE_1",
    [WITH_EXCEPT_START] = "WITH_EXCEPT_START",
    [GET_AITER] = "GET_AITER",
    [GET_ANEXT] = "GET_ANEXT",
    [BEFORE_ASYNC_WITH] = "BEFORE_ASYNC_WITH",
    [BEFORE_WITH] = "BEFORE_WITH",
    [END_ASYNC_FOR] = "END_ASYNC_FOR",
    [CLEANUP_THROW] = "CLEANUP_THROW",
    [CALL_NO_KW_TYPE_1] = "CALL_NO_KW_TYPE_1",
    [COMPARE_OP_FLOAT] = "COMPARE_OP_FLOAT",
    [COMPARE_OP_INT] = "COMPARE_OP_INT",
    [COMPARE_OP_STR] = "COMPARE_OP_STR",
    [STORE_SUBSCR] = "STORE_SUBSCR",
    [DELETE_SUBSCR] = "DELETE_SUBSCR",
    [FOR_ITER_LIST] = "FOR_ITER_LIST",
    [FOR_ITER_TUPLE] = "FOR_ITER_TUPLE",
    [FOR_ITER_RANGE] = "FOR_ITER_RANGE",
    [FOR_ITER_GEN] = "FOR_ITER_GEN",
    [BB_TEST_ITER_LIST] = "BB_TEST_ITER_LIST",
    [BB_TEST_ITER_TUPLE] = "BB_TEST_ITER_TUPLE",
    [GET_ITER] = "GET_ITER",
    [GET_YIELD_FROM_ITER] = "GET_YIELD_FROM_ITER",
    [BB_TEST_ITER_RANGE] = "BB_TEST_ITER_RANGE",
    [LOAD_BUILD_CLASS] = "LOAD_BUILD_CLASS",
    [BB_TEST_ITER_GEN] = "BB_TEST_ITER_GEN",
    [LOAD_ATTR_CLASS] = "LOAD_ATTR_CLASS",
    [LOAD_ASSERTION_ERROR] = "LOAD_ASSERTION_ERROR",
    [RETURN_GENERATOR] = "RETURN_GENERATOR",
    [LOAD_ATTR_GETATTRIBUTE_OVERRIDDEN] = "LOAD_ATTR_GETATTRIBUTE_OVERRIDDEN",
    [LOAD_ATTR_INSTANCE_VALUE] = "LOAD_ATTR_INSTANCE_VALUE",
    [LOAD_ATTR_MODULE] = "LOAD_ATTR_MODULE",
    [LOAD_ATTR_PROPERTY] = "LOAD_ATTR_PROPERTY",
    [LOAD_ATTR_SLOT] = "LOAD_ATTR_SLOT",
    [LOAD_ATTR_WITH_HINT] = "LOAD_ATTR_WITH_HINT",
    [LOAD_ATTR_METHOD_LAZY_DICT] = "LOAD_ATTR_METHOD_LAZY_DICT",
    [RETURN_VALUE] = "RETURN_VALUE",
    [LOAD_ATTR_METHOD_NO_DICT] = "LOAD_ATTR_METHOD_NO_DICT",
    [SETUP_ANNOTATIONS] = "SETUP_ANNOTATIONS",
    [LOAD_ATTR_METHOD_WITH_VALUES] = "LOAD_ATTR_METHOD_WITH_VALUES",
    [LOAD_CONST__LOAD_FAST] = "LOAD_CONST__LOAD_FAST",
    [LOAD_FAST__LOAD_CONST] = "LOAD_FAST__LOAD_CONST",
    [POP_EXCEPT] = "POP_EXCEPT",
    [STORE_NAME] = "STORE_NAME",
    [DELETE_NAME] = "DELETE_NAME",
    [UNPACK_SEQUENCE] = "UNPACK_SEQUENCE",
    [FOR_ITER] = "FOR_ITER",
    [UNPACK_EX] = "UNPACK_EX",
    [STORE_ATTR] = "STORE_ATTR",
    [DELETE_ATTR] = "DELETE_ATTR",
    [STORE_GLOBAL] = "STORE_GLOBAL",
    [DELETE_GLOBAL] = "DELETE_GLOBAL",
    [SWAP] = "SWAP",
    [LOAD_CONST] = "LOAD_CONST",
    [LOAD_NAME] = "LOAD_NAME",
    [BUILD_TUPLE] = "BUILD_TUPLE",
    [BUILD_LIST] = "BUILD_LIST",
    [BUILD_SET] = "BUILD_SET",
    [BUILD_MAP] = "BUILD_MAP",
    [LOAD_ATTR] = "LOAD_ATTR",
    [COMPARE_OP] = "COMPARE_OP",
    [IMPORT_NAME] = "IMPORT_NAME",
    [IMPORT_FROM] = "IMPORT_FROM",
    [JUMP_FORWARD] = "JUMP_FORWARD",
    [LOAD_FAST__LOAD_FAST] = "LOAD_FAST__LOAD_FAST",
    [LOAD_GLOBAL_BUILTIN] = "LOAD_GLOBAL_BUILTIN",
    [LOAD_GLOBAL_MODULE] = "LOAD_GLOBAL_MODULE",
    [POP_JUMP_IF_FALSE] = "POP_JUMP_IF_FALSE",
    [POP_JUMP_IF_TRUE] = "POP_JUMP_IF_TRUE",
    [LOAD_GLOBAL] = "LOAD_GLOBAL",
    [IS_OP] = "IS_OP",
    [CONTAINS_OP] = "CONTAINS_OP",
    [RERAISE] = "RERAISE",
    [COPY] = "COPY",
    [RETURN_CONST] = "RETURN_CONST",
    [BINARY_OP] = "BINARY_OP",
    [SEND] = "SEND",
    [LOAD_FAST] = "LOAD_FAST",
    [STORE_FAST] = "STORE_FAST",
    [DELETE_FAST] = "DELETE_FAST",
    [LOAD_FAST_CHECK] = "LOAD_FAST_CHECK",
    [POP_JUMP_IF_NOT_NONE] = "POP_JUMP_IF_NOT_NONE",
    [POP_JUMP_IF_NONE] = "POP_JUMP_IF_NONE",
    [RAISE_VARARGS] = "RAISE_VARARGS",
    [GET_AWAITABLE] = "GET_AWAITABLE",
    [MAKE_FUNCTION] = "MAKE_FUNCTION",
    [BUILD_SLICE] = "BUILD_SLICE",
    [JUMP_BACKWARD_NO_INTERRUPT] = "JUMP_BACKWARD_NO_INTERRUPT",
    [MAKE_CELL] = "MAKE_CELL",
    [LOAD_CLOSURE] = "LOAD_CLOSURE",
    [LOAD_DEREF] = "LOAD_DEREF",
    [STORE_DEREF] = "STORE_DEREF",
    [DELETE_DEREF] = "DELETE_DEREF",
    [JUMP_BACKWARD] = "JUMP_BACKWARD",
    [STORE_ATTR_INSTANCE_VALUE] = "STORE_ATTR_INSTANCE_VALUE",
    [CALL_FUNCTION_EX] = "CALL_FUNCTION_EX",
    [STORE_ATTR_SLOT] = "STORE_ATTR_SLOT",
    [EXTENDED_ARG] = "EXTENDED_ARG",
    [LIST_APPEND] = "LIST_APPEND",
    [SET_ADD] = "SET_ADD",
    [MAP_ADD] = "MAP_ADD",
    [LOAD_CLASSDEREF] = "LOAD_CLASSDEREF",
    [COPY_FREE_VARS] = "COPY_FREE_VARS",
    [YIELD_VALUE] = "YIELD_VALUE",
    [RESUME] = "RESUME",
    [MATCH_CLASS] = "MATCH_CLASS",
    [STORE_ATTR_WITH_HINT] = "STORE_ATTR_WITH_HINT",
    [STORE_FAST__LOAD_FAST] = "STORE_FAST__LOAD_FAST",
    [FORMAT_VALUE] = "FORMAT_VALUE",
    [BUILD_CONST_KEY_MAP] = "BUILD_CONST_KEY_MAP",
    [BUILD_STRING] = "BUILD_STRING",
    [STORE_FAST__STORE_FAST] = "STORE_FAST__STORE_FAST",
    [STORE_SUBSCR_DICT] = "STORE_SUBSCR_DICT",
    [STORE_SUBSCR_LIST_INT] = "STORE_SUBSCR_LIST_INT",
    [UNPACK_SEQUENCE_LIST] = "UNPACK_SEQUENCE_LIST",
    [LIST_EXTEND] = "LIST_EXTEND",
    [SET_UPDATE] = "SET_UPDATE",
    [DICT_MERGE] = "DICT_MERGE",
    [DICT_UPDATE] = "DICT_UPDATE",
    [UNPACK_SEQUENCE_TUPLE] = "UNPACK_SEQUENCE_TUPLE",
    [UNPACK_SEQUENCE_TWO_TUPLE] = "UNPACK_SEQUENCE_TWO_TUPLE",
    [SEND_GEN] = "SEND_GEN",
    [BB_BRANCH] = "BB_BRANCH",
    [BB_BRANCH_IF_FLAG_UNSET] = "BB_BRANCH_IF_FLAG_UNSET",
    [CALL] = "CALL",
    [KW_NAMES] = "KW_NAMES",
    [CALL_INTRINSIC_1] = "CALL_INTRINSIC_1",
    [CALL_INTRINSIC_2] = "CALL_INTRINSIC_2",
    [BB_BRANCH_IF_FLAG_SET] = "BB_BRANCH_IF_FLAG_SET",
    [BB_JUMP_IF_FLAG_UNSET] = "BB_JUMP_IF_FLAG_UNSET",
    [BB_JUMP_IF_FLAG_SET] = "BB_JUMP_IF_FLAG_SET",
    [BB_TEST_ITER] = "BB_TEST_ITER",
    [BB_TEST_ITER_RANGE] = "BB_TEST_ITER_RANGE",
    [BB_TEST_ITER_LIST] = "BB_TEST_ITER_LIST",
    [BB_TEST_ITER_TUPLE] = "BB_TEST_ITER_TUPLE",
    [BB_TEST_POP_IF_FALSE] = "BB_TEST_POP_IF_FALSE",
    [BB_TEST_POP_IF_TRUE] = "BB_TEST_POP_IF_TRUE",
    [BB_TEST_POP_IF_NOT_NONE] = "BB_TEST_POP_IF_NOT_NONE",
    [BB_TEST_POP_IF_NONE] = "BB_TEST_POP_IF_NONE",
    [BB_JUMP_BACKWARD_LAZY] = "BB_JUMP_BACKWARD_LAZY",
    [BINARY_CHECK_INT] = "BINARY_CHECK_INT",
    [BINARY_CHECK_FLOAT] = "BINARY_CHECK_FLOAT",
    [CHECK_LIST] = "CHECK_LIST",
    [BINARY_OP_ADD_INT_REST] = "BINARY_OP_ADD_INT_REST",
    [BINARY_OP_ADD_FLOAT_UNBOXED] = "BINARY_OP_ADD_FLOAT_UNBOXED",
    [BINARY_OP_SUBTRACT_INT_REST] = "BINARY_OP_SUBTRACT_INT_REST",
    [BINARY_OP_SUBTRACT_FLOAT_UNBOXED] = "BINARY_OP_SUBTRACT_FLOAT_UNBOXED",
    [BINARY_OP_MULTIPLY_INT_REST] = "BINARY_OP_MULTIPLY_INT_REST",
    [BINARY_OP_MULTIPLY_FLOAT_UNBOXED] = "BINARY_OP_MULTIPLY_FLOAT_UNBOXED",
    [BINARY_SUBSCR_LIST_INT_REST] = "BINARY_SUBSCR_LIST_INT_REST",
    [STORE_SUBSCR_LIST_INT_REST] = "STORE_SUBSCR_LIST_INT_REST",
    [POP_TOP_NO_DECREF] = "POP_TOP_NO_DECREF",
    [UNBOX_FLOAT] = "UNBOX_FLOAT",
    [BOX_FLOAT] = "BOX_FLOAT",
    [COPY_NO_INCREF] = "COPY_NO_INCREF",
    [LOAD_FAST_NO_INCREF] = "LOAD_FAST_NO_INCREF",
    [STORE_FAST_BOXED_UNBOXED] = "STORE_FAST_BOXED_UNBOXED",
    [STORE_FAST_UNBOXED_BOXED] = "STORE_FAST_UNBOXED_BOXED",
    [STORE_FAST_UNBOXED_UNBOXED] = "STORE_FAST_UNBOXED_UNBOXED",
    [206] = "<206>",
    [207] = "<207>",
    [208] = "<208>",
    [209] = "<209>",
    [210] = "<210>",
    [211] = "<211>",
    [212] = "<212>",
    [213] = "<213>",
    [214] = "<214>",
    [215] = "<215>",
    [216] = "<216>",
    [217] = "<217>",
    [218] = "<218>",
    [219] = "<219>",
    [220] = "<220>",
    [221] = "<221>",
    [222] = "<222>",
    [223] = "<223>",
    [224] = "<224>",
    [225] = "<225>",
    [226] = "<226>",
    [227] = "<227>",
    [228] = "<228>",
    [229] = "<229>",
    [230] = "<230>",
    [231] = "<231>",
    [232] = "<232>",
    [233] = "<233>",
    [234] = "<234>",
    [235] = "<235>",
    [236] = "<236>",
    [237] = "<237>",
    [238] = "<238>",
    [239] = "<239>",
    [240] = "<240>",
    [241] = "<241>",
    [242] = "<242>",
    [243] = "<243>",
    [244] = "<244>",
    [245] = "<245>",
    [246] = "<246>",
    [247] = "<247>",
    [248] = "<248>",
    [249] = "<249>",
    [250] = "<250>",
    [251] = "<251>",
    [252] = "<252>",
    [253] = "<253>",
    [254] = "<254>",
    [DO_TRACING] = "DO_TRACING",
    [SETUP_FINALLY] = "SETUP_FINALLY",
    [SETUP_CLEANUP] = "SETUP_CLEANUP",
    [SETUP_WITH] = "SETUP_WITH",
    [POP_BLOCK] = "POP_BLOCK",
    [JUMP] = "JUMP",
    [JUMP_NO_INTERRUPT] = "JUMP_NO_INTERRUPT",
    [LOAD_METHOD] = "LOAD_METHOD",
};
#endif


#define EXTRA_CASES \
    case 206: \
    case 207: \
    case 208: \
    case 209: \
    case 210: \
    case 211: \
    case 212: \
    case 213: \
    case 214: \
    case 215: \
    case 216: \
    case 217: \
    case 218: \
    case 219: \
    case 220: \
    case 221: \
    case 222: \
    case 223: \
    case 224: \
    case 225: \
    case 226: \
    case 227: \
    case 228: \
    case 229: \
    case 230: \
    case 231: \
    case 232: \
    case 233: \
    case 234: \
    case 235: \
    case 236: \
    case 237: \
    case 238: \
    case 239: \
    case 240: \
    case 241: \
    case 242: \
    case 243: \
    case 244: \
    case 245: \
    case 246: \
    case 247: \
    case 248: \
    case 249: \
    case 250: \
    case 251: \
    case 252: \
    case 253: \
    case 254: \
        ;

#ifdef __cplusplus
}
#endif
#endif  // !Py_INTERNAL_OPCODE_H
