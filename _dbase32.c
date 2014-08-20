/*
dbase32: base32-encoding with a sorted-order alphabet (for databases)
Copyright (C) 2013 Novacut Inc

This file is part of `dbase32`.

`dbase32` is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

`dbase32` is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License along
with `dbase32`.  If not, see <http://www.gnu.org/licenses/>.

Authors:
    Jason Gerard DeRose <jderose@novacut.com>
*/

#include <Python.h>

#define MAX_BIN_LEN 60
#define MAX_TXT_LEN 96
#define DB32_END 89

static const uint8_t DB32_FORWARD[32] = "3456789ABCDEFGHIJKLMNOPQRSTUVWXY";
static const uint8_t DB32_REVERSE[256] = {
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,
      0,  // '3' [51]
      1,  // '4' [52]
      2,  // '5' [53]
      3,  // '6' [54]
      4,  // '7' [55]
      5,  // '8' [56]
      6,  // '9' [57]
    255,  // ':' [58]
    255,  // ';' [59]
    255,  // '<' [60]
    255,  // '=' [61]
    255,  // '>' [62]
    255,  // '?' [63]
    255,  // '@' [64]
      7,  // 'A' [65]
      8,  // 'B' [66]
      9,  // 'C' [67]
     10,  // 'D' [68]
     11,  // 'E' [69]
     12,  // 'F' [70]
     13,  // 'G' [71]
     14,  // 'H' [72]
     15,  // 'I' [73]
     16,  // 'J' [74]
     17,  // 'K' [75]
     18,  // 'L' [76]
     19,  // 'M' [77]
     20,  // 'N' [78]
     21,  // 'O' [79]
     22,  // 'P' [80]
     23,  // 'Q' [81]
     24,  // 'R' [82]
     25,  // 'S' [83]
     26,  // 'T' [84]
     27,  // 'U' [85]
     28,  // 'V' [86]
     29,  // 'W' [87]
     30,  // 'X' [88]
     31,  // 'Y' [89]
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
    255,255,255,255,255,255,255,255,255,255,255,255,255,255,
};


/* dbase32_encode()

Return value is the status:
    status == 0 means success
    status == 1 means invalid bin_len
    status == 2 means invalid txt_len */
static uint8_t
dbase32_encode(const size_t bin_len, const uint8_t *bin_buf,
               const size_t txt_len,       uint8_t *txt_buf)
{
    size_t block, count;
    uint64_t taxi;

    if (bin_len < 5 || bin_len > MAX_BIN_LEN || bin_len % 5 != 0) {
        return 1;
    }
    if (txt_len != bin_len * 8 / 5) {
        return 2;
    }
    count = bin_len / 5;
    for (block=0; block < count; block++) {
        // Pack 40 bits into the taxi (8 bits at a time):
        taxi = bin_buf[0];
        taxi = bin_buf[1] | (taxi << 8);
        taxi = bin_buf[2] | (taxi << 8);
        taxi = bin_buf[3] | (taxi << 8);
        taxi = bin_buf[4] | (taxi << 8);

        // Unpack 40 bits from the taxi (5 bits at a time):
        txt_buf[0] = DB32_FORWARD[(taxi >> 35) & 31];
        txt_buf[1] = DB32_FORWARD[(taxi >> 30) & 31];
        txt_buf[2] = DB32_FORWARD[(taxi >> 25) & 31];
        txt_buf[3] = DB32_FORWARD[(taxi >> 20) & 31];
        txt_buf[4] = DB32_FORWARD[(taxi >> 15) & 31];
        txt_buf[5] = DB32_FORWARD[(taxi >> 10) & 31];
        txt_buf[6] = DB32_FORWARD[(taxi >>  5) & 31];
        txt_buf[7] = DB32_FORWARD[taxi & 31];

        // Move the pointers:
        bin_buf += 5;
        txt_buf += 8;
    }
    return 0;
}


/*
 * dbase32_decode(txt_len, txt_buf, bin_len, bin_buf) => status
 *
 * `dbase32_db32dec()` uses this function.
 *
 * Return value is the status:
 *      status == 0 means success
 *      status == 1 means txt_len is invalid
 *      status == 2 means bin_len is invalid
 *      status >= 3 means txt_buf contains one or more invalid letters
 *
 */
static inline uint8_t
dbase32_decode(const size_t txt_len, const uint8_t *txt_buf,
               const size_t bin_len,       uint8_t *bin_buf)
{
    size_t block, count;
    uint8_t r;
    uint64_t taxi;

    if (txt_len < 8 || txt_len > MAX_TXT_LEN || txt_len % 8 != 0) {
        return 1;
    }
    if (bin_len != txt_len * 5 / 8) {
        return 2;
    }

    /*
     * To mitigate timing attacks, we always decode the entire buffer, and then
     * do a single error check on the final value of `r`.
     *
     * However, use of the DB32_REVERSE table means this function still leaks
     * information through cache misses, etc.
     */
    count = txt_len / 8;
    for (r = block = 0; block < count; block++) {
        /* Pack 40 bits into the taxi (5 bits at a time) */
        r = DB32_REVERSE[txt_buf[0]] | (r & 224);    taxi = r;
        r = DB32_REVERSE[txt_buf[1]] | (r & 224);    taxi = r | (taxi << 5);
        r = DB32_REVERSE[txt_buf[2]] | (r & 224);    taxi = r | (taxi << 5);
        r = DB32_REVERSE[txt_buf[3]] | (r & 224);    taxi = r | (taxi << 5);
        r = DB32_REVERSE[txt_buf[4]] | (r & 224);    taxi = r | (taxi << 5);
        r = DB32_REVERSE[txt_buf[5]] | (r & 224);    taxi = r | (taxi << 5);
        r = DB32_REVERSE[txt_buf[6]] | (r & 224);    taxi = r | (taxi << 5);
        r = DB32_REVERSE[txt_buf[7]] | (r & 224);    taxi = r | (taxi << 5);

        /* Unpack 40 bits from the taxi (8 bits at a time) */
        bin_buf[0] = (taxi >> 32) & 255;
        bin_buf[1] = (taxi >> 24) & 255;
        bin_buf[2] = (taxi >> 16) & 255;
        bin_buf[3] = (taxi >>  8) & 255;
        bin_buf[4] = taxi & 255;

        /* Move the pointers */
        txt_buf += 8;
        bin_buf += 5;
    }

    /* 
     * Return value is (r & 244):
     *
     *       31: 00011111 <= bits set in DB32_REVERSE for valid characters
     *      224: 11100000 <= bits set in DB32_REVERSE for invalid characters
     */
    return (r & 224);
}


/*
 * dbase32_invalid(txt_len, txt_buf) => status
 *
 * Both `dbase32_isdb32()` and `dbase32_check_db32()` use this function.
 *
 * Return value is the status:
 *      status == 0: valid Dbase32
 *      status == 1: txt_len is invalid
 *      status > 1: txt_buf contains one or more invalid Dbase32 letters
 *
 */
static inline uint8_t
dbase32_invalid(const size_t txt_len, const uint8_t *txt_buf)
{
    size_t block, count;
    uint8_t r;

    if (txt_len < 8 || txt_len > MAX_TXT_LEN || txt_len % 8 != 0) {
        return 1;
    }

    /*
     * To mitigate timing attacks, we always scan the entire buffer, and then do
     * a single error check on the final value of `r`.
     *
     * However, use of the DB32_REVERSE table means this function still leaks
     * information through cache misses, etc.
     */
    count = txt_len / 8;
    for (r = block = 0; block < count; block++) {
        r |= DB32_REVERSE[txt_buf[0]];
        r |= DB32_REVERSE[txt_buf[1]];
        r |= DB32_REVERSE[txt_buf[2]];
        r |= DB32_REVERSE[txt_buf[3]];
        r |= DB32_REVERSE[txt_buf[4]];
        r |= DB32_REVERSE[txt_buf[5]];
        r |= DB32_REVERSE[txt_buf[6]];
        r |= DB32_REVERSE[txt_buf[7]];
        txt_buf += 8;  /* Move the pointer */
    }

    /* 
     * Return value is (r & 244):
     *
     *       31: 00011111 <= bits set in DB32_REVERSE for valid characters
     *      224: 11100000 <= bits set in DB32_REVERSE for invalid characters
     */
    return (r & 224);
}


static PyObject *
dbase32_db32enc(PyObject *self, PyObject *args)
{
    Py_buffer pybuf;
    PyObject *pyret;
    const uint8_t *bin_buf;
    uint8_t *txt_buf;
    size_t bin_len, txt_len;
    uint8_t status;

    // Strictly validate, we only accept well-formed IDs:
    if (!PyArg_ParseTuple(args, "y*:db32enc", &pybuf)) {
        return NULL;
    }
    bin_buf = pybuf.buf;
    bin_len = pybuf.len;
    if (bin_len < 5 || bin_len > MAX_BIN_LEN) {
        PyErr_Format(PyExc_ValueError,
            "len(data) is %u, need 5 <= len(data) <= %u", bin_len, MAX_BIN_LEN
        );
        PyBuffer_Release(&pybuf);
        return NULL;
    }
    if (bin_len % 5 != 0) {
        PyErr_Format(PyExc_ValueError,
            "len(data) is %u, need len(data) % 5 == 0", bin_len
        );
        PyBuffer_Release(&pybuf);
        return NULL;
    }

    // Allocate destination buffer:
    txt_len = bin_len * 8 / 5;
    pyret = PyUnicode_New(txt_len, DB32_END);
    if (pyret == NULL ) {
        PyBuffer_Release(&pybuf);
        return NULL;
    }
    txt_buf = (uint8_t *)PyUnicode_1BYTE_DATA(pyret);

    // dbase32_encode() returns 0 on success:
    status = dbase32_encode(bin_len, bin_buf, txt_len, txt_buf);
    PyBuffer_Release(&pybuf);
    if (status != 0) {
        PyErr_SetString(PyExc_RuntimeError, "something went very wrong");
        Py_DECREF(pyret);
        return NULL;
    }
    return pyret;
}


static PyObject *
dbase32_db32dec(PyObject *self, PyObject *args)
{
    PyObject *pyret = NULL;
    const uint8_t *txt_buf;
    uint8_t *bin_buf;
    size_t txt_len = 0;  // Note: the "s#" format requires initializing to zero
    size_t bin_len;

    // Strictly validate, we only accept well-formed IDs:
    if (!PyArg_ParseTuple(args, "s#:db32dec", &txt_buf, &txt_len)) {
        return NULL;
    }
    if (txt_len < 8 || txt_len > MAX_TXT_LEN) {
        PyErr_Format(PyExc_ValueError,
            "len(text) is %u, need 8 <= len(text) <= %u", txt_len, MAX_TXT_LEN
        );
        return NULL;
    }
    if (txt_len % 8 != 0) {
        PyErr_Format(PyExc_ValueError,
            "len(text) is %u, need len(text) % 8 == 0", txt_len
        );
        return NULL;
    }

    // Allocate destination buffer:
    bin_len = txt_len * 5 / 8;
    pyret = PyBytes_FromStringAndSize(NULL, bin_len);
    if (pyret == NULL) {
        return NULL;
    }
    bin_buf = (uint8_t *)PyBytes_AS_STRING(pyret);

    // dbase32_decode() returns 0 on success:
    if (dbase32_decode(txt_len, txt_buf, bin_len, bin_buf) != 0) {
        Py_CLEAR(pyret);
        PyObject *borrowed = PyTuple_GetItem(args, 0);
        PyErr_Format(PyExc_ValueError, "invalid Dbase32: %R", borrowed);
    }
    return pyret;
}


static PyObject *
dbase32_isdb32(PyObject *self, PyObject *args)
{
    const uint8_t *txt_buf = NULL;
    size_t txt_len = 0;

    if (!PyArg_ParseTuple(args, "s#:isdb32", &txt_buf, &txt_len)) {
        return NULL;
    }
    if (txt_len < 8 || txt_len > MAX_TXT_LEN || txt_len % 8 != 0) {
        Py_RETURN_FALSE;
    }
    if (dbase32_invalid(txt_len, txt_buf)) {
        Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}


static PyObject *
dbase32_check_db32(PyObject *self, PyObject *args)
{
    const uint8_t *txt_buf = NULL;
    size_t txt_len = 0;  // Note: the "s#" format requires initializing to zero

    if (!PyArg_ParseTuple(args, "s#:check_db32", &txt_buf, &txt_len)) {
        return NULL;
    }

    // Check that len(text) is valid:
    if (txt_len < 8 || txt_len > MAX_TXT_LEN) {
        PyErr_Format(PyExc_ValueError,
            "len(text) is %u, need 8 <= len(text) <= %u", txt_len, MAX_TXT_LEN
        );
        return NULL;
    }
    if (txt_len % 8 != 0) {
        PyErr_Format(PyExc_ValueError,
            "len(text) is %u, need len(text) % 8 == 0", txt_len
        );
        return NULL;
    }

    // Check that text contains only valid Dbase32 letters:
    if (dbase32_invalid(txt_len, txt_buf)) {
        PyObject *borrowed = PyTuple_GetItem(args, 0);
        PyErr_Format(PyExc_ValueError, "invalid Dbase32: %R", borrowed);
        return NULL;
    }

    Py_RETURN_NONE;
}


static PyObject *
dbase32_random_id(PyObject *self, PyObject *args, PyObject *kw)
{
    static char *keys[] = {"numbytes", NULL};
    size_t numbytes = 15;
    PyObject *pyret;
    uint8_t *bin_buf, *txt_buf;
    size_t txt_len;
    int status;

    if (!PyArg_ParseTupleAndKeywords(args, kw, "|n:random_id", keys, &numbytes)) {
        return NULL;
    }
    if (numbytes < 5 || numbytes > MAX_BIN_LEN) {
        PyErr_Format(PyExc_ValueError,
            "numbytes is %u, need 5 <= numbytes <= %u", numbytes, MAX_BIN_LEN
        );
        return NULL;
    }
    if (numbytes % 5 != 0) {
        PyErr_Format(PyExc_ValueError,
            "numbytes is %u, need numbytes % 5 == 0", numbytes
        );
        return NULL;
    }

    // Allocate temp buffer for binary ID:
    bin_buf = (uint8_t *)malloc(numbytes * sizeof(uint8_t));
    if (bin_buf == NULL) {
        return PyErr_NoMemory();
    }

    // Get random bytes from /dev/urandom:
    status = _PyOS_URandom(bin_buf, numbytes);
    if (status == -1) {
        free(bin_buf);
        return NULL;
    }

    // Allocate destination buffer:
    txt_len = numbytes * 8 / 5;
    pyret = PyUnicode_New(txt_len, DB32_END);
    if (pyret == NULL ) {
        free(bin_buf);
        return NULL;
    }
    txt_buf = (uint8_t *)PyUnicode_1BYTE_DATA(pyret);

    // dbase32_encode() returns 0 on success:
    status = dbase32_encode(numbytes, bin_buf, txt_len, txt_buf);
    free(bin_buf);
    if (status != 0) {
        PyErr_SetString(PyExc_RuntimeError, "something went very wrong");
        Py_DECREF(pyret);
        return NULL;
    }
    return pyret;
}


static PyObject *
dbase32_time_id(PyObject *self, PyObject *args, PyObject *kw)
{
    static char *keys[] = {"timestamp", NULL};
    double timestamp = -1;
    PyObject *pyret;
    uint32_t ts;
    uint8_t *bin_buf, *txt_buf;
    int status;

    if (!PyArg_ParseTupleAndKeywords(args, kw, "|d:time_id", keys, &timestamp)) {
        return NULL;
    }
    if (timestamp < 0) {
        timestamp = (double)time(NULL);
    }

    // Allocate temp buffer for binary ID:
    bin_buf = (uint8_t *)malloc(15 * sizeof(uint8_t));
    if (bin_buf == NULL) {
        return PyErr_NoMemory();
    }

    // First 4 bytes are from timestamp:
    ts = (uint32_t)timestamp;
    bin_buf[0] = (ts >> 24) & 255;
    bin_buf[1] = (ts >> 16) & 255;
    bin_buf[2] = (ts >>  8) & 255;
    bin_buf[3] = ts & 255;

    // Next 11 bytes are from os.urandom():
    status = _PyOS_URandom(bin_buf + 4, 11);
    if (status == -1) {
        free(bin_buf);
        return NULL;
    }

    // Allocate destination buffer:
    pyret = PyUnicode_New(24, DB32_END);
    if (pyret == NULL ) {
        free(bin_buf);
        return NULL;
    }
    txt_buf = (uint8_t *)PyUnicode_1BYTE_DATA(pyret);

    // dbase32_encode() returns 0 on success:
    status = dbase32_encode(15, bin_buf, 24, txt_buf);
    free(bin_buf);
    if (status != 0) {
        PyErr_SetString(PyExc_RuntimeError, "something went very wrong");
        Py_DECREF(pyret);
        return NULL;
    }
    return pyret;
}


/* module init */
static struct PyMethodDef dbase32_functions[] = {
    {"db32enc", dbase32_db32enc, METH_VARARGS, "db32enc(data)"},
    {"db32dec", dbase32_db32dec, METH_VARARGS, "db32dec(text)"},
    {"isdb32", dbase32_isdb32, METH_VARARGS, "isdb32(text)"},
    {"check_db32", dbase32_check_db32, METH_VARARGS, "check_db32(text)"},
    {"random_id", (PyCFunction)dbase32_random_id, METH_VARARGS | METH_KEYWORDS, 
        "random_id(numbytes=15)"},
    {"time_id", (PyCFunction)dbase32_time_id, METH_VARARGS | METH_KEYWORDS, 
        "time_id(timestamp=-1)"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef dbase32 = {
    PyModuleDef_HEAD_INIT,
    "_dbase32",
    NULL,
    -1,
    dbase32_functions
};

PyMODINIT_FUNC
PyInit__dbase32(void)
{
    return PyModule_Create(&dbase32);
}
