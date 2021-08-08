/* cursor.c - the cursor type
 *
 * Copyright (C) 2004-2010 Gerhard Häring <gh@ghaering.de>
 *
 * This file is part of pysqlite.
 *
 * This software is provided 'as-is', without any express or implied
 * warranty.  In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 * 1. The origin of this software must not be misrepresented; you must not
 *    claim that you wrote the original software. If you use this software
 *    in a product, an acknowledgment in the product documentation would be
 *    appreciated but is not required.
 * 2. Altered source versions must be plainly marked as such, and must not be
 *    misrepresented as being the original software.
 * 3. This notice may not be removed or altered from any source distribution.
 */

#include "cursor.h"
#include "module.h"
#include "util.h"

#define clinic_state() (pysqlite_get_state(NULL))
#include "clinic/cursor.c.h"
#undef clinic_state

/*[clinic input]
module _sqlite3
class _sqlite3.Cursor "pysqlite_Cursor *" "clinic_state()->CursorType"
[clinic start generated code]*/
/*[clinic end generated code: output=da39a3ee5e6b4b0d input=3c5b8115c5cf30f1]*/

static const char errmsg_fetch_across_rollback[] = "Cursor needed to be reset because of commit/rollback and can no longer be fetched from.";

/*[clinic input]
_sqlite3.Cursor.__init__ as pysqlite_cursor_init

    connection: object(type='pysqlite_Connection *', subclass_of='clinic_state()->ConnectionType')
    /

[clinic start generated code]*/

static int
pysqlite_cursor_init_impl(pysqlite_Cursor *self,
                          pysqlite_Connection *connection)
/*[clinic end generated code: output=ac59dce49a809ca8 input=23d4265b534989fb]*/
{
    Py_INCREF(connection);
    Py_XSETREF(self->connection, connection);
    Py_CLEAR(self->statement);
    Py_CLEAR(self->next_row);
    Py_CLEAR(self->row_cast_map);

    Py_INCREF(Py_None);
    Py_XSETREF(self->description, Py_None);

    Py_INCREF(Py_None);
    Py_XSETREF(self->lastrowid, Py_None);

    self->arraysize = 1;
    self->closed = 0;
    self->reset = 0;

    self->rowcount = -1L;

    Py_INCREF(Py_None);
    Py_XSETREF(self->row_factory, Py_None);

    if (!pysqlite_check_thread(self->connection)) {
        return -1;
    }

    if (!pysqlite_connection_register_cursor(connection, (PyObject*)self)) {
        return -1;
    }

    self->initialized = 1;

    return 0;
}

static int
cursor_traverse(pysqlite_Cursor *self, visitproc visit, void *arg)
{
    Py_VISIT(Py_TYPE(self));
    Py_VISIT(self->connection);
    Py_VISIT(self->description);
    Py_VISIT(self->row_cast_map);
    Py_VISIT(self->lastrowid);
    Py_VISIT(self->row_factory);
    Py_VISIT(self->statement);
    Py_VISIT(self->next_row);
    return 0;
}

static int
cursor_clear(pysqlite_Cursor *self)
{
    Py_CLEAR(self->connection);
    Py_CLEAR(self->description);
    Py_CLEAR(self->row_cast_map);
    Py_CLEAR(self->lastrowid);
    Py_CLEAR(self->row_factory);
    if (self->statement) {
        /* Reset the statement if the user has not closed the cursor */
        pysqlite_statement_reset(self->statement);
        Py_CLEAR(self->statement);
    }
    Py_CLEAR(self->next_row);

    return 0;
}

static void
cursor_dealloc(pysqlite_Cursor *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    PyObject_GC_UnTrack(self);
    if (self->in_weakreflist != NULL) {
        PyObject_ClearWeakRefs((PyObject*)self);
    }
    tp->tp_clear((PyObject *)self);
    tp->tp_free(self);
    Py_DECREF(tp);
}

static PyObject *
_pysqlite_get_converter(pysqlite_state *state, const char *keystr,
                        Py_ssize_t keylen)
{
    PyObject *key;
    PyObject *upcase_key;
    PyObject *retval;
    _Py_IDENTIFIER(upper);

    key = PyUnicode_FromStringAndSize(keystr, keylen);
    if (!key) {
        return NULL;
    }
    upcase_key = _PyObject_CallMethodIdNoArgs(key, &PyId_upper);
    Py_DECREF(key);
    if (!upcase_key) {
        return NULL;
    }

    retval = PyDict_GetItemWithError(state->converters, upcase_key);
    Py_DECREF(upcase_key);

    return retval;
}

static int
pysqlite_build_row_cast_map(pysqlite_Cursor* self)
{
    int i;
    const char* pos;
    const char* decltype;
    PyObject* converter;

    if (!self->connection->detect_types) {
        return 0;
    }

    Py_XSETREF(self->row_cast_map, PyList_New(0));
    if (!self->row_cast_map) {
        return -1;
    }

    for (i = 0; i < sqlite3_column_count(self->statement->st); i++) {
        converter = NULL;

        if (self->connection->detect_types & PARSE_COLNAMES) {
            const char *colname = sqlite3_column_name(self->statement->st, i);
            if (colname == NULL) {
                PyErr_NoMemory();
                Py_CLEAR(self->row_cast_map);
                return -1;
            }
            const char *type_start = NULL;
            for (pos = colname; *pos != 0; pos++) {
                if (*pos == '[') {
                    type_start = pos + 1;
                }
                else if (*pos == ']' && type_start != NULL) {
                    pysqlite_state *state = self->connection->state;
                    converter = _pysqlite_get_converter(state, type_start,
                                                        pos - type_start);
                    if (!converter && PyErr_Occurred()) {
                        Py_CLEAR(self->row_cast_map);
                        return -1;
                    }
                    break;
                }
            }
        }

        if (!converter && self->connection->detect_types & PARSE_DECLTYPES) {
            decltype = sqlite3_column_decltype(self->statement->st, i);
            if (decltype) {
                for (pos = decltype;;pos++) {
                    /* Converter names are split at '(' and blanks.
                     * This allows 'INTEGER NOT NULL' to be treated as 'INTEGER' and
                     * 'NUMBER(10)' to be treated as 'NUMBER', for example.
                     * In other words, it will work as people expect it to work.*/
                    if (*pos == ' ' || *pos == '(' || *pos == 0) {
                        pysqlite_state *state = self->connection->state;
                        converter = _pysqlite_get_converter(state, decltype,
                                                            pos - decltype);
                        if (!converter && PyErr_Occurred()) {
                            Py_CLEAR(self->row_cast_map);
                            return -1;
                        }
                        break;
                    }
                }
            }
        }

        if (!converter) {
            converter = Py_None;
        }

        if (PyList_Append(self->row_cast_map, converter) != 0) {
            Py_CLEAR(self->row_cast_map);
            return -1;
        }
    }

    return 0;
}

static PyObject *
_pysqlite_build_column_name(pysqlite_Cursor *self, const char *colname)
{
    const char* pos;
    Py_ssize_t len;

    if (self->connection->detect_types & PARSE_COLNAMES) {
        for (pos = colname; *pos; pos++) {
            if (*pos == '[') {
                if ((pos != colname) && (*(pos-1) == ' ')) {
                    pos--;
                }
                break;
            }
        }
        len = pos - colname;
    }
    else {
        len = strlen(colname);
    }
    return PyUnicode_FromStringAndSize(colname, len);
}

/*
 * Returns a row from the currently active SQLite statement
 *
 * Precondidition:
 * - sqlite3_step() has been called before and it returned SQLITE_ROW.
 */
static PyObject *
_pysqlite_fetch_one_row(pysqlite_Cursor* self)
{
    int i, numcols;
    PyObject* row;
    int coltype;
    PyObject* converter;
    PyObject* converted;
    Py_ssize_t nbytes;
    char buf[200];
    const char* colname;
    PyObject* error_msg;

    if (self->reset) {
        PyObject *exc = self->connection->InterfaceError;
        PyErr_SetString(exc, errmsg_fetch_across_rollback);
        return NULL;
    }

    Py_BEGIN_ALLOW_THREADS
    numcols = sqlite3_data_count(self->statement->st);
    Py_END_ALLOW_THREADS

    row = PyTuple_New(numcols);
    if (!row)
        return NULL;

    sqlite3 *db = self->connection->db;
    for (i = 0; i < numcols; i++) {
        if (self->connection->detect_types
                && self->row_cast_map != NULL
                && i < PyList_GET_SIZE(self->row_cast_map))
        {
            converter = PyList_GET_ITEM(self->row_cast_map, i);
        }
        else {
            converter = Py_None;
        }

        /*
         * Note, sqlite3_column_bytes() must come after sqlite3_column_blob()
         * or sqlite3_column_text().
         *
         * See https://sqlite.org/c3ref/column_blob.html for details.
         */
        if (converter != Py_None) {
            const void *blob = sqlite3_column_blob(self->statement->st, i);
            if (blob == NULL) {
                if (sqlite3_errcode(db) == SQLITE_NOMEM) {
                    PyErr_NoMemory();
                    goto error;
                }
                converted = Py_NewRef(Py_None);
            }
            else {
                nbytes = sqlite3_column_bytes(self->statement->st, i);
                PyObject *item = PyBytes_FromStringAndSize(blob, nbytes);
                if (item == NULL) {
                    goto error;
                }
                converted = PyObject_CallOneArg(converter, item);
                Py_DECREF(item);
            }
        } else {
            Py_BEGIN_ALLOW_THREADS
            coltype = sqlite3_column_type(self->statement->st, i);
            Py_END_ALLOW_THREADS
            if (coltype == SQLITE_NULL) {
                converted = Py_NewRef(Py_None);
            } else if (coltype == SQLITE_INTEGER) {
                converted = PyLong_FromLongLong(sqlite3_column_int64(self->statement->st, i));
            } else if (coltype == SQLITE_FLOAT) {
                converted = PyFloat_FromDouble(sqlite3_column_double(self->statement->st, i));
            } else if (coltype == SQLITE_TEXT) {
                const char *text = (const char*)sqlite3_column_text(self->statement->st, i);
                if (text == NULL && sqlite3_errcode(db) == SQLITE_NOMEM) {
                    PyErr_NoMemory();
                    goto error;
                }

                nbytes = sqlite3_column_bytes(self->statement->st, i);
                if (self->connection->text_factory == (PyObject*)&PyUnicode_Type) {
                    converted = PyUnicode_FromStringAndSize(text, nbytes);
                    if (!converted && PyErr_ExceptionMatches(PyExc_UnicodeDecodeError)) {
                        PyErr_Clear();
                        colname = sqlite3_column_name(self->statement->st, i);
                        if (colname == NULL) {
                            PyErr_NoMemory();
                            goto error;
                        }
                        PyOS_snprintf(buf, sizeof(buf) - 1, "Could not decode to UTF-8 column '%s' with text '%s'",
                                     colname , text);
                        error_msg = PyUnicode_Decode(buf, strlen(buf), "ascii", "replace");

                        PyObject *exc = self->connection->OperationalError;
                        if (!error_msg) {
                            PyErr_SetString(exc, "Could not decode to UTF-8");
                        } else {
                            PyErr_SetObject(exc, error_msg);
                            Py_DECREF(error_msg);
                        }
                    }
                } else if (self->connection->text_factory == (PyObject*)&PyBytes_Type) {
                    converted = PyBytes_FromStringAndSize(text, nbytes);
                } else if (self->connection->text_factory == (PyObject*)&PyByteArray_Type) {
                    converted = PyByteArray_FromStringAndSize(text, nbytes);
                } else {
                    converted = PyObject_CallFunction(self->connection->text_factory, "y#", text, nbytes);
                }
            } else {
                /* coltype == SQLITE_BLOB */
                const void *blob = sqlite3_column_blob(self->statement->st, i);
                if (blob == NULL && sqlite3_errcode(db) == SQLITE_NOMEM) {
                    PyErr_NoMemory();
                    goto error;
                }

                nbytes = sqlite3_column_bytes(self->statement->st, i);
                converted = PyBytes_FromStringAndSize(blob, nbytes);
            }
        }

        if (!converted) {
            goto error;
        }
        PyTuple_SET_ITEM(row, i, converted);
    }

    if (PyErr_Occurred())
        goto error;

    return row;

error:
    Py_DECREF(row);
    return NULL;
}

/*
 * Checks if a cursor object is usable.
 *
 * 0 => error; 1 => ok
 */
static int check_cursor(pysqlite_Cursor* cur)
{
    if (!cur->initialized) {
        pysqlite_state *state = pysqlite_get_state_by_type(Py_TYPE(cur));
        PyErr_SetString(state->ProgrammingError,
                        "Base Cursor.__init__ not called.");
        return 0;
    }

    if (cur->closed) {
        PyErr_SetString(cur->connection->state->ProgrammingError,
                        "Cannot operate on a closed cursor.");
        return 0;
    }

    if (cur->locked) {
        PyErr_SetString(cur->connection->state->ProgrammingError,
                        "Recursive use of cursors not allowed.");
        return 0;
    }

    return pysqlite_check_thread(cur->connection) && pysqlite_check_connection(cur->connection);
}

static int
begin_transaction(pysqlite_Connection *self)
{
    int rc;
    sqlite3_stmt *statement;

    Py_BEGIN_ALLOW_THREADS
    rc = sqlite3_prepare_v2(self->db, self->begin_statement, -1, &statement,
                            NULL);
    Py_END_ALLOW_THREADS

    if (rc != SQLITE_OK) {
        _pysqlite_seterror(self->state, self->db);
        goto error;
    }

    Py_BEGIN_ALLOW_THREADS
    sqlite3_step(statement);
    rc = sqlite3_finalize(statement);
    Py_END_ALLOW_THREADS

    if (rc != SQLITE_OK && !PyErr_Occurred()) {
        _pysqlite_seterror(self->state, self->db);
    }

error:
    if (PyErr_Occurred()) {
        return -1;
    }
    return 0;
}

static PyObject *
get_statement_from_cache(pysqlite_Cursor *self, PyObject *operation)
{
    PyObject *args[] = { operation, };
    PyObject *cache = self->connection->statement_cache;
    return PyObject_Vectorcall(cache, args, 1, NULL);
}

static PyObject *
_pysqlite_query_execute(pysqlite_Cursor* self, int multiple, PyObject* operation, PyObject* second_argument)
{
    PyObject* parameters_list = NULL;
    PyObject* parameters_iter = NULL;
    PyObject* parameters = NULL;
    int i;
    int rc;
    int numcols;
    PyObject* column_name;
    sqlite_int64 lastrowid;

    if (!check_cursor(self)) {
        goto error;
    }

    self->locked = 1;
    self->reset = 0;

    Py_CLEAR(self->next_row);

    if (multiple) {
        if (PyIter_Check(second_argument)) {
            /* iterator */
            parameters_iter = Py_NewRef(second_argument);
        } else {
            /* sequence */
            parameters_iter = PyObject_GetIter(second_argument);
            if (!parameters_iter) {
                goto error;
            }
        }
    } else {
        parameters_list = PyList_New(0);
        if (!parameters_list) {
            goto error;
        }

        if (second_argument == NULL) {
            second_argument = PyTuple_New(0);
            if (!second_argument) {
                goto error;
            }
        } else {
            Py_INCREF(second_argument);
        }
        if (PyList_Append(parameters_list, second_argument) != 0) {
            Py_DECREF(second_argument);
            goto error;
        }
        Py_DECREF(second_argument);

        parameters_iter = PyObject_GetIter(parameters_list);
        if (!parameters_iter) {
            goto error;
        }
    }

    if (self->statement != NULL) {
        /* There is an active statement */
        pysqlite_statement_reset(self->statement);
    }

    /* reset description and rowcount */
    Py_INCREF(Py_None);
    Py_SETREF(self->description, Py_None);
    self->rowcount = 0L;

    if (self->statement) {
        (void)pysqlite_statement_reset(self->statement);
    }

    PyObject *stmt = get_statement_from_cache(self, operation);
    Py_XSETREF(self->statement, (pysqlite_Statement *)stmt);
    if (!self->statement) {
        goto error;
    }

    if (self->statement->in_use) {
        Py_SETREF(self->statement,
                  pysqlite_statement_create(self->connection, operation));
        if (self->statement == NULL) {
            goto error;
        }
    }

    pysqlite_statement_reset(self->statement);
    pysqlite_statement_mark_dirty(self->statement);

    /* We start a transaction implicitly before a DML statement.
       SELECT is the only exception. See #9924. */
    if (self->connection->begin_statement
        && self->statement->is_dml
        && sqlite3_get_autocommit(self->connection->db))
    {
        if (begin_transaction(self->connection) < 0) {
            goto error;
        }
    }

    pysqlite_state *state = self->connection->state;
    while (1) {
        parameters = PyIter_Next(parameters_iter);
        if (!parameters) {
            break;
        }

        pysqlite_statement_mark_dirty(self->statement);

        pysqlite_statement_bind_parameters(state, self->statement, parameters);
        if (PyErr_Occurred()) {
            goto error;
        }

        rc = pysqlite_step(self->statement->st);
        if (rc != SQLITE_DONE && rc != SQLITE_ROW) {
            if (PyErr_Occurred()) {
                /* there was an error that occurred in a user-defined callback */
                if (state->enable_callback_tracebacks) {
                    PyErr_Print();
                } else {
                    PyErr_Clear();
                }
            }
            (void)pysqlite_statement_reset(self->statement);
            _pysqlite_seterror(state, self->connection->db);
            goto error;
        }

        if (pysqlite_build_row_cast_map(self) != 0) {
            _PyErr_FormatFromCause(state->OperationalError,
                                   "Error while building row_cast_map");
            goto error;
        }

        assert(rc == SQLITE_ROW || rc == SQLITE_DONE);
        Py_BEGIN_ALLOW_THREADS
        numcols = sqlite3_column_count(self->statement->st);
        Py_END_ALLOW_THREADS
        if (self->description == Py_None && numcols > 0) {
            Py_SETREF(self->description, PyTuple_New(numcols));
            if (!self->description) {
                goto error;
            }
            for (i = 0; i < numcols; i++) {
                const char *colname;
                colname = sqlite3_column_name(self->statement->st, i);
                if (colname == NULL) {
                    PyErr_NoMemory();
                    goto error;
                }
                column_name = _pysqlite_build_column_name(self, colname);
                if (column_name == NULL) {
                    goto error;
                }
                PyObject *descriptor = PyTuple_Pack(7, column_name,
                                                    Py_None, Py_None, Py_None,
                                                    Py_None, Py_None, Py_None);
                Py_DECREF(column_name);
                if (descriptor == NULL) {
                    goto error;
                }
                PyTuple_SET_ITEM(self->description, i, descriptor);
            }
        }

        if (self->statement->is_dml) {
            self->rowcount += (long)sqlite3_changes(self->connection->db);
        } else {
            self->rowcount= -1L;
        }

        if (!multiple) {
            Py_BEGIN_ALLOW_THREADS
            lastrowid = sqlite3_last_insert_rowid(self->connection->db);
            Py_END_ALLOW_THREADS
            Py_SETREF(self->lastrowid, PyLong_FromLongLong(lastrowid));
            if (self->lastrowid == NULL) {
                goto error;
            }
        }

        if (rc == SQLITE_ROW) {
            if (multiple) {
                PyErr_SetString(state->ProgrammingError,
                                "executemany() can only execute DML "
                                "statements.");
                goto error;
            }

            self->next_row = _pysqlite_fetch_one_row(self);
            if (self->next_row == NULL)
                goto error;
        } else if (rc == SQLITE_DONE && !multiple) {
            pysqlite_statement_reset(self->statement);
            Py_CLEAR(self->statement);
        }

        if (multiple) {
            pysqlite_statement_reset(self->statement);
        }
        Py_XDECREF(parameters);
    }

error:
    Py_XDECREF(parameters);
    Py_XDECREF(parameters_iter);
    Py_XDECREF(parameters_list);

    self->locked = 0;

    if (PyErr_Occurred()) {
        self->rowcount = -1L;
        return NULL;
    } else {
        return Py_NewRef((PyObject *)self);
    }
}

/*[clinic input]
_sqlite3.Cursor.execute as pysqlite_cursor_execute

    sql: unicode
    parameters: object(c_default = 'NULL') = ()
    /

Executes a SQL statement.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_execute_impl(pysqlite_Cursor *self, PyObject *sql,
                             PyObject *parameters)
/*[clinic end generated code: output=d81b4655c7c0bbad input=91d7bb36f127f597]*/
{
    return _pysqlite_query_execute(self, 0, sql, parameters);
}

/*[clinic input]
_sqlite3.Cursor.executemany as pysqlite_cursor_executemany

    sql: unicode
    seq_of_parameters: object
    /

Repeatedly executes a SQL statement.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_executemany_impl(pysqlite_Cursor *self, PyObject *sql,
                                 PyObject *seq_of_parameters)
/*[clinic end generated code: output=2c65a3c4733fb5d8 input=440707b7af87fba8]*/
{
    return _pysqlite_query_execute(self, 1, sql, seq_of_parameters);
}

/*[clinic input]
_sqlite3.Cursor.executescript as pysqlite_cursor_executescript

    sql_script: str
    /

Executes multiple SQL statements at once. Non-standard.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_executescript_impl(pysqlite_Cursor *self,
                                   const char *sql_script)
/*[clinic end generated code: output=8fd726dde1c65164 input=1ac0693dc8db02a8]*/
{
    _Py_IDENTIFIER(commit);
    sqlite3_stmt* statement;
    int rc;
    size_t sql_len;
    PyObject* result;

    if (!check_cursor(self)) {
        return NULL;
    }

    self->reset = 0;

    sql_len = strlen(sql_script);
    int max_length = sqlite3_limit(self->connection->db,
                                   SQLITE_LIMIT_LENGTH, -1);
    if (sql_len >= (unsigned)max_length) {
        PyErr_SetString(self->connection->DataError,
                        "query string is too large");
        return NULL;
    }

    /* commit first */
    result = _PyObject_CallMethodIdNoArgs((PyObject *)self->connection, &PyId_commit);
    if (!result) {
        goto error;
    }
    Py_DECREF(result);

    pysqlite_state *state = self->connection->state;
    while (1) {
        const char *tail;

        Py_BEGIN_ALLOW_THREADS
        rc = sqlite3_prepare_v2(self->connection->db,
                                sql_script,
                                (int)sql_len + 1,
                                &statement,
                                &tail);
        Py_END_ALLOW_THREADS
        if (rc != SQLITE_OK) {
            _pysqlite_seterror(state, self->connection->db);
            goto error;
        }

        /* execute statement, and ignore results of SELECT statements */
        do {
            rc = pysqlite_step(statement);
            if (PyErr_Occurred()) {
                (void)sqlite3_finalize(statement);
                goto error;
            }
        } while (rc == SQLITE_ROW);

        if (rc != SQLITE_DONE) {
            (void)sqlite3_finalize(statement);
            _pysqlite_seterror(state, self->connection->db);
            goto error;
        }

        rc = sqlite3_finalize(statement);
        if (rc != SQLITE_OK) {
            _pysqlite_seterror(state, self->connection->db);
            goto error;
        }

        if (*tail == (char)0) {
            break;
        }
        sql_len -= (tail - sql_script);
        sql_script = tail;
    }

error:
    if (PyErr_Occurred()) {
        return NULL;
    } else {
        return Py_NewRef((PyObject *)self);
    }
}

static PyObject *
pysqlite_cursor_iternext(pysqlite_Cursor *self)
{
    PyObject* next_row_tuple;
    PyObject* next_row;
    int rc;

    if (!check_cursor(self)) {
        return NULL;
    }

    if (self->reset) {
        PyObject *exc = self->connection->InterfaceError;
        PyErr_SetString(exc, errmsg_fetch_across_rollback);
        return NULL;
    }

    if (!self->next_row) {
         if (self->statement) {
            (void)pysqlite_statement_reset(self->statement);
            Py_CLEAR(self->statement);
        }
        return NULL;
    }

    next_row_tuple = self->next_row;
    assert(next_row_tuple != NULL);
    self->next_row = NULL;

    if (self->row_factory != Py_None) {
        next_row = PyObject_CallFunction(self->row_factory, "OO", self, next_row_tuple);
        if (next_row == NULL) {
            self->next_row = next_row_tuple;
            return NULL;
        }
        Py_DECREF(next_row_tuple);
    } else {
        next_row = next_row_tuple;
    }

    if (self->statement) {
        rc = pysqlite_step(self->statement->st);
        if (PyErr_Occurred()) {
            (void)pysqlite_statement_reset(self->statement);
            Py_DECREF(next_row);
            return NULL;
        }
        if (rc != SQLITE_DONE && rc != SQLITE_ROW) {
            (void)pysqlite_statement_reset(self->statement);
            Py_DECREF(next_row);
            _pysqlite_seterror(self->connection->state, self->connection->db);
            return NULL;
        }

        if (rc == SQLITE_ROW) {
            self->next_row = _pysqlite_fetch_one_row(self);
            if (self->next_row == NULL) {
                (void)pysqlite_statement_reset(self->statement);
                return NULL;
            }
        }
    }

    return next_row;
}

/*[clinic input]
_sqlite3.Cursor.fetchone as pysqlite_cursor_fetchone

Fetches one row from the resultset.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_fetchone_impl(pysqlite_Cursor *self)
/*[clinic end generated code: output=4bd2eabf5baaddb0 input=e78294ec5980fdba]*/
{
    PyObject* row;

    row = pysqlite_cursor_iternext(self);
    if (!row && !PyErr_Occurred()) {
        Py_RETURN_NONE;
    }

    return row;
}

/*[clinic input]
_sqlite3.Cursor.fetchmany as pysqlite_cursor_fetchmany

    size as maxrows: int(c_default='self->arraysize') = 1
        The default value is set by the Cursor.arraysize attribute.

Fetches several rows from the resultset.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_fetchmany_impl(pysqlite_Cursor *self, int maxrows)
/*[clinic end generated code: output=a8ef31fea64d0906 input=c26e6ca3f34debd0]*/
{
    PyObject* row;
    PyObject* list;
    int counter = 0;

    list = PyList_New(0);
    if (!list) {
        return NULL;
    }

    while ((row = pysqlite_cursor_iternext(self))) {
        if (PyList_Append(list, row) < 0) {
            Py_DECREF(row);
            break;
        }
        Py_DECREF(row);

        if (++counter == maxrows) {
            break;
        }
    }

    if (PyErr_Occurred()) {
        Py_DECREF(list);
        return NULL;
    } else {
        return list;
    }
}

/*[clinic input]
_sqlite3.Cursor.fetchall as pysqlite_cursor_fetchall

Fetches all rows from the resultset.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_fetchall_impl(pysqlite_Cursor *self)
/*[clinic end generated code: output=d5da12aca2da4b27 input=f5d401086a8df25a]*/
{
    PyObject* row;
    PyObject* list;

    list = PyList_New(0);
    if (!list) {
        return NULL;
    }

    while ((row = pysqlite_cursor_iternext(self))) {
        if (PyList_Append(list, row) < 0) {
            Py_DECREF(row);
            break;
        }
        Py_DECREF(row);
    }

    if (PyErr_Occurred()) {
        Py_DECREF(list);
        return NULL;
    } else {
        return list;
    }
}

/*[clinic input]
_sqlite3.Cursor.setinputsizes as pysqlite_cursor_setinputsizes

    sizes: object
    /

Required by DB-API. Does nothing in pysqlite.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_setinputsizes(pysqlite_Cursor *self, PyObject *sizes)
/*[clinic end generated code: output=893c817afe9d08ad input=7cffbb168663bc69]*/
{
    Py_RETURN_NONE;
}

/*[clinic input]
_sqlite3.Cursor.setoutputsize as pysqlite_cursor_setoutputsize

    size: object
    column: object = None
    /

Required by DB-API. Does nothing in pysqlite.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_setoutputsize_impl(pysqlite_Cursor *self, PyObject *size,
                                   PyObject *column)
/*[clinic end generated code: output=018d7e9129d45efe input=077b017da58b9389]*/
{
    Py_RETURN_NONE;
}

/*[clinic input]
_sqlite3.Cursor.close as pysqlite_cursor_close

    cls: defining_class

Closes the cursor.
[clinic start generated code]*/

static PyObject *
pysqlite_cursor_close_impl(pysqlite_Cursor *self, PyTypeObject *cls)
/*[clinic end generated code: output=a08ab3d772f45438 input=28ba9b532ab46ba0]*/
{
    if (!self->connection) {
        pysqlite_state *state = pysqlite_get_state_by_cls(cls);
        PyErr_SetString(state->ProgrammingError,
                        "Base Cursor.__init__ not called.");
        return NULL;
    }
    if (!pysqlite_check_thread(self->connection) || !pysqlite_check_connection(self->connection)) {
        return NULL;
    }

    if (self->statement) {
        (void)pysqlite_statement_reset(self->statement);
        Py_CLEAR(self->statement);
    }

    self->closed = 1;

    Py_RETURN_NONE;
}

static PyMethodDef cursor_methods[] = {
    PYSQLITE_CURSOR_CLOSE_METHODDEF
    PYSQLITE_CURSOR_EXECUTEMANY_METHODDEF
    PYSQLITE_CURSOR_EXECUTESCRIPT_METHODDEF
    PYSQLITE_CURSOR_EXECUTE_METHODDEF
    PYSQLITE_CURSOR_FETCHALL_METHODDEF
    PYSQLITE_CURSOR_FETCHMANY_METHODDEF
    PYSQLITE_CURSOR_FETCHONE_METHODDEF
    PYSQLITE_CURSOR_SETINPUTSIZES_METHODDEF
    PYSQLITE_CURSOR_SETOUTPUTSIZE_METHODDEF
    {NULL, NULL}
};

static struct PyMemberDef cursor_members[] =
{
    {"connection", T_OBJECT, offsetof(pysqlite_Cursor, connection), READONLY},
    {"description", T_OBJECT, offsetof(pysqlite_Cursor, description), READONLY},
    {"arraysize", T_INT, offsetof(pysqlite_Cursor, arraysize), 0},
    {"lastrowid", T_OBJECT, offsetof(pysqlite_Cursor, lastrowid), READONLY},
    {"rowcount", T_LONG, offsetof(pysqlite_Cursor, rowcount), READONLY},
    {"row_factory", T_OBJECT, offsetof(pysqlite_Cursor, row_factory), 0},
    {"__weaklistoffset__", T_PYSSIZET, offsetof(pysqlite_Cursor, in_weakreflist), READONLY},
    {NULL}
};

static const char cursor_doc[] =
PyDoc_STR("SQLite database cursor class.");

static PyType_Slot cursor_slots[] = {
    {Py_tp_dealloc, cursor_dealloc},
    {Py_tp_doc, (void *)cursor_doc},
    {Py_tp_iter, PyObject_SelfIter},
    {Py_tp_iternext, pysqlite_cursor_iternext},
    {Py_tp_methods, cursor_methods},
    {Py_tp_members, cursor_members},
    {Py_tp_init, pysqlite_cursor_init},
    {Py_tp_traverse, cursor_traverse},
    {Py_tp_clear, cursor_clear},
    {0, NULL},
};

static PyType_Spec cursor_spec = {
    .name = MODULE_NAME ".Cursor",
    .basicsize = sizeof(pysqlite_Cursor),
    .flags = (Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE |
              Py_TPFLAGS_HAVE_GC | Py_TPFLAGS_IMMUTABLETYPE),
    .slots = cursor_slots,
};

int
pysqlite_cursor_setup_types(PyObject *module)
{
    PyObject *type = PyType_FromModuleAndSpec(module, &cursor_spec, NULL);
    if (type == NULL) {
        return -1;
    }
    pysqlite_state *state = pysqlite_get_state(module);
    state->CursorType = (PyTypeObject *)type;
    return 0;
}
