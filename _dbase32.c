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
#include <string.h>

#define MAX_DATA 60
#define MAX_TEXT 96

#define MAX_BINLEN 60
#define MAX_TXT_LEN 96

#define START 51
#define END 89

static const uint8_t forward[32] = "3456789ABCDEFGHIJKLMNOPQRSTUVWXY";

static const uint8_t reverse[39] = {
      0,  // 51 '3'
      1,  // 52 '4'
      2,  // 53 '5'
      3,  // 54 '6'
      4,  // 55 '7'
      5,  // 56 '8'
      6,  // 57 '9'
    255,  // 58 ':'
    255,  // 59 ';'
    255,  // 60 '<'
    255,  // 61 '='
    255,  // 62 '>'
    255,  // 63 '?'
    255,  // 64 '@'
      7,  // 65 'A'
      8,  // 66 'B'
      9,  // 67 'C'
     10,  // 68 'D'
     11,  // 69 'E'
     12,  // 70 'F'
     13,  // 71 'G'
     14,  // 72 'H'
     15,  // 73 'I'
     16,  // 74 'J'
     17,  // 75 'K'
     18,  // 76 'L'
     19,  // 77 'M'
     20,  // 78 'N'
     21,  // 79 'O'
     22,  // 80 'P'
     23,  // 81 'Q'
     24,  // 82 'R'
     25,  // 83 'S'
     26,  // 84 'T'
     27,  // 85 'U'
     28,  // 86 'V'
     29,  // 87 'W'
     30,  // 88 'X'
     31,  // 89 'Y'
};


static PyObject *
dbase32_db32enc(PyObject *self, PyObject *args)
{
    Py_buffer buf;
    size_t len, i, j;
    const uint8_t *src;
    uint8_t *dst;
    uint16_t taxi = 0;
    uint8_t bits = 0;
    PyObject *rv;

    // Strictly validate, we only accept well-formed IDs:
    if (!PyArg_ParseTuple(args, "y*:db32enc", &buf)) {
        return NULL;
    }
    src = buf.buf;
    len = buf.len;
    if (len < 5 || len > MAX_DATA) {
        PyErr_Format(PyExc_ValueError, "need 5 <= len(data) <= %u", MAX_DATA);
        PyBuffer_Release(&buf);
        return NULL;
    }
    if (len % 5 != 0) {
        PyErr_SetString(PyExc_ValueError, "need len(data) % 5 == 0");
        PyBuffer_Release(&buf);
        return NULL;
    }

    // Let's do it:
    if ((rv=PyUnicode_New(len * 8 / 5, END)) == NULL ) {
        PyBuffer_Release(&buf);
        return NULL;
    }
    dst = (uint8_t *)PyUnicode_1BYTE_DATA(rv);
    for (i=j=0; i<len; i++) {
        taxi = (taxi << 8) | src[i];
        bits += 8;
        while (bits >= 5) {
            bits -= 5;
            dst[j] = forward[(taxi >> bits) & 0x1f];
            j++;
        }
    }
    PyBuffer_Release(&buf);

    // Sanity check:
    if (bits != 0 || j != len * 8 / 5) {
        PyErr_SetString(PyExc_RuntimeError, "something went very wrong");
        Py_DECREF(rv);
        return NULL;
    }
    return rv;
}


static int
base32_decode(const size_t txt_len, const uint8_t *txt_buf,
              const size_t bin_len, uint8_t *bin_buf)
{
    /*
    Return value is the status:
        status >=  0 means invalid base32 letter (char is returned)
        status == -1 means success
        status == -2 means invalid txt_len
        status == -3 means wrong bin_len
        status <= -4 means internal error
    */
    size_t i, j;
    uint8_t c, r;
    uint16_t taxi = 0;
    uint8_t bits = 0;

    if (txt_len < 8 || txt_len > MAX_TXT_LEN || txt_len % 8 != 0) {
        return -2;  // invalid txt_len
    }
    if (bin_len != txt_len * 5 / 8) {
        return -3;  // wrong bin_len 
    }
    for (i = j = 0; i < txt_len; i++) {
        c = txt_buf[i];
        if (c < START || c > END) {
            return c;  // invalid base32 letter
        }
        r = reverse[c - START];
        if (r > 31) {
            return c;  // invalid base32 letter (internal in reverse table)
        }
        taxi = (taxi << 5) | r;
        bits += 5;
        while (bits >= 8) {
            bits -= 8;
            bin_buf[j] = (taxi >> bits) & 0xff;
            j++;
        }
    }
    if (bits != 0 || j != bin_len || i != txt_len) {
        return -4;  // internal error
    }
    return -1;  // success
}


static PyObject *
dbase32_db32dec(PyObject *self, PyObject *args)
{
    const uint8_t *txt_buf;
    uint8_t *bin_buf;
    size_t txt_len, bin_len;
    int status;
    PyObject *rv;

    // Strictly validate, we only accept well-formed IDs:
    if (!PyArg_ParseTuple(args, "s:db32dec", &txt_buf)) {
        return NULL;
    }
    txt_len = strlen(txt_buf);
    if (txt_len < 8 || txt_len > MAX_TXT_LEN) {
        PyErr_Format(PyExc_ValueError,
            "need 8 <= len(text) <= %u", MAX_TXT_LEN
        );
        return NULL;
    }
    if (txt_len % 8 != 0) {
        PyErr_SetString(PyExc_ValueError, "need len(text) % 8 == 0");
        return NULL;
    }

    // Allocate destination buffer:
    bin_len = txt_len * 5 / 8;
    if ((rv=PyBytes_FromStringAndSize(NULL, bin_len)) == NULL) {
        return NULL;
    }
    bin_buf = (uint8_t *)PyBytes_AS_STRING(rv);

    // base32_decode() returns -1 on success:
    status = base32_decode(txt_len, txt_buf, bin_len, bin_buf);
    if (status != -1) {
        if (status >= 0) {
            PyErr_Format(PyExc_ValueError,
                "invalid base32 letter: %c", status
            );
        }
        else {
            PyErr_SetString(PyExc_RuntimeError, "something went very wrong");
        }
        Py_DECREF(rv);
        return NULL;
    }
    return rv;
}


/* module init */
static struct PyMethodDef dbase32_functions[] = {
    {"db32enc", dbase32_db32enc, METH_VARARGS, "db32enc(data)"},
    {"db32dec", dbase32_db32dec, METH_VARARGS, "db32dec(text)"},
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
