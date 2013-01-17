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

#define MAX_BIN_LEN 60
#define MAX_TXT_LEN 96

/*
    encode_x() can encode to an arbitrary base32 alphabet by giving it an
    appropriate forward-table.

    decode_x() can decode the same when given the corresponding reverse-table,
    plus the corresponding start and end character values.

    Neither function attempts to validate the tables in anyway, both functions
    assume the tables are well-formed.  The tables are not expected to be
    directly provided via user input, or even external API.  The tables are
    static, pre-calculated values.

    The gen.py script is used to create these tables... they should *not* be
    created by hand!
*/

// DB32: Dmedia-Base32: non-standard 3-9, A-Y letters (sorted)
// [removes 0, 1, 2, Z]
static const uint8_t DB32_START = 51;
static const uint8_t DB32_END = 89;
static const uint8_t DB32_FORWARD[32] = "3456789ABCDEFGHIJKLMNOPQRSTUVWXY";
static const uint8_t DB32_REVERSE[39] = {
      0,  // 51 '3' [ 0]
      1,  // 52 '4' [ 1]
      2,  // 53 '5' [ 2]
      3,  // 54 '6' [ 3]
      4,  // 55 '7' [ 4]
      5,  // 56 '8' [ 5]
      6,  // 57 '9' [ 6]
    255,  // 58 ':' [ 7]
    255,  // 59 ';' [ 8]
    255,  // 60 '<' [ 9]
    255,  // 61 '=' [10]
    255,  // 62 '>' [11]
    255,  // 63 '?' [12]
    255,  // 64 '@' [13]
      7,  // 65 'A' [14]
      8,  // 66 'B' [15]
      9,  // 67 'C' [16]
     10,  // 68 'D' [17]
     11,  // 69 'E' [18]
     12,  // 70 'F' [19]
     13,  // 71 'G' [20]
     14,  // 72 'H' [21]
     15,  // 73 'I' [22]
     16,  // 74 'J' [23]
     17,  // 75 'K' [24]
     18,  // 76 'L' [25]
     19,  // 77 'M' [26]
     20,  // 78 'N' [27]
     21,  // 79 'O' [28]
     22,  // 80 'P' [29]
     23,  // 81 'Q' [30]
     24,  // 82 'R' [31]
     25,  // 83 'S' [32]
     26,  // 84 'T' [33]
     27,  // 85 'U' [34]
     28,  // 86 'V' [35]
     29,  // 87 'W' [36]
     30,  // 88 'X' [37]
     31,  // 89 'Y' [38]
};

// SB32: Sorted-Base32: standard RFC-3548 letters, but in sorted order
// [removes 0, 1, 8, 9]
static const uint8_t SB32_START = 50;
static const uint8_t SB32_END = 90;
static const uint8_t SB32_FORWARD[32] = "234567ABCDEFGHIJKLMNOPQRSTUVWXYZ";
static const uint8_t SB32_REVERSE[41] = {
      0,  // 50 '2' [ 0]
      1,  // 51 '3' [ 1]
      2,  // 52 '4' [ 2]
      3,  // 53 '5' [ 3]
      4,  // 54 '6' [ 4]
      5,  // 55 '7' [ 5]
    255,  // 56 '8' [ 6]
    255,  // 57 '9' [ 7]
    255,  // 58 ':' [ 8]
    255,  // 59 ';' [ 9]
    255,  // 60 '<' [10]
    255,  // 61 '=' [11]
    255,  // 62 '>' [12]
    255,  // 63 '?' [13]
    255,  // 64 '@' [14]
      6,  // 65 'A' [15]
      7,  // 66 'B' [16]
      8,  // 67 'C' [17]
      9,  // 68 'D' [18]
     10,  // 69 'E' [19]
     11,  // 70 'F' [20]
     12,  // 71 'G' [21]
     13,  // 72 'H' [22]
     14,  // 73 'I' [23]
     15,  // 74 'J' [24]
     16,  // 75 'K' [25]
     17,  // 76 'L' [26]
     18,  // 77 'M' [27]
     19,  // 78 'N' [28]
     20,  // 79 'O' [29]
     21,  // 80 'P' [30]
     22,  // 81 'Q' [31]
     23,  // 82 'R' [32]
     24,  // 83 'S' [33]
     25,  // 84 'T' [34]
     26,  // 85 'U' [35]
     27,  // 86 'V' [36]
     28,  // 87 'W' [37]
     29,  // 88 'X' [38]
     30,  // 89 'Y' [39]
     31,  // 90 'Z' [40]
};


/* encode_x(): encode using alphabet defined by x_forward

Return value is the status:
    status == 0 means success
    status == 1 means invalid bin_len
    status == 2 means wrong txt_len
    status == 3 means internal error
*/
static uint8_t
encode_x(const size_t bin_len, const uint8_t *bin_buf,
         const size_t txt_len, uint8_t *txt_buf,
         const uint8_t *x_forward)
{
    size_t i, j;
    uint16_t taxi = 0;
    uint8_t bits = 0;

    if (bin_len < 5 || bin_len > MAX_BIN_LEN || bin_len % 5 != 0) {
        return 1;
    }
    if (txt_len != bin_len * 8 / 5) {
        return 2;
    }
    for (i = j = 0; i < bin_len; i++) {
        taxi = (taxi << 8) | bin_buf[i];
        bits += 8;
        while (bits >= 5) {
            bits -= 5;
            txt_buf[j] = x_forward[(taxi >> bits) & 31];
            j++;
        }
    }
    if (bits != 0 || j != txt_len || i != bin_len) {
        return 3;
    }
    return 0;
}


/* decode_x(): decode using alphabet defined by x_reverse, x_start, x_end

Return value is the status:
    status >=  0 means invalid base32 letter (char is returned)
    status == -1 means success
    status == -2 means invalid txt_len
    status == -3 means wrong bin_len
    status == -4 means internal error
*/
static int
decode_x(const size_t txt_len, const uint8_t *txt_buf,
         const size_t bin_len, uint8_t *bin_buf,
         const uint8_t *x_reverse, const char x_start, const char x_end)
{
    size_t i, j;
    uint8_t c, r;
    uint16_t taxi = 0;
    uint8_t bits = 0;

    if (txt_len < 8 || txt_len > MAX_TXT_LEN || txt_len % 8 != 0) {
        return -2;
    }
    if (bin_len != txt_len * 5 / 8) {
        return -3;
    }
    for (i = j = 0; i < txt_len; i++) {
        c = txt_buf[i];
        if (c < x_start || c > x_end) {
            return c;  // invalid base32 letter
        }
        r = x_reverse[c - x_start];
        if (r > 31) {
            return c;  // invalid base32 letter (internal in reverse table)
        }
        taxi = (taxi << 5) | r;
        bits += 5;
        while (bits >= 8) {
            bits -= 8;
            bin_buf[j] = (taxi >> bits) & 255;
            j++;
        }
    }
    if (bits != 0 || j != bin_len || i != txt_len) {
        return -4;
    }
    return -1;
}


/* Experimental decoder that doesn't use a reverse table

     3   9     A   Y
    51  57    65  89
    ======    ======
      51        58
*/
static int
decode_db32(const size_t txt_len, const uint8_t *txt_buf,
         const size_t bin_len, uint8_t *bin_buf)
{
    size_t i, j;
    uint8_t c, r;
    uint16_t taxi = 0;
    uint8_t bits = 0;

    if (txt_len < 8 || txt_len > MAX_TXT_LEN || txt_len % 8 != 0) {
        return -2;
    }
    if (bin_len != txt_len * 5 / 8) {
        return -3;
    }
    for (i = j = 0; i < txt_len; i++) {
        c = txt_buf[i];
        if (c > 89) {
            return c;
        }
        if (c >= 65) {
            r = c - 58;
        }
        else if (c >= 51 && c <= 57) {
            r = c - 51;
        }
        else {
            return c;
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
        return -4;
    }
    return -1;
}


static PyObject *
dbase32_db32enc(PyObject *self, PyObject *args)
{
    Py_buffer pybuf;
    PyObject *pyrv;
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
    if ((pyrv=PyUnicode_New(txt_len, DB32_END)) == NULL ) {
        PyBuffer_Release(&pybuf);
        return NULL;
    }
    txt_buf = (uint8_t *)PyUnicode_1BYTE_DATA(pyrv);

    // encode_x() returns 0 on success:
    status = encode_x(
        bin_len, bin_buf, txt_len, txt_buf,
        DB32_FORWARD
    );
    PyBuffer_Release(&pybuf);
    if (status != 0) {
        PyErr_SetString(PyExc_RuntimeError, "something went very wrong");
        Py_DECREF(pyrv);
        return NULL;
    }
    return pyrv;
}


static PyObject *
dbase32_db32dec(PyObject *self, PyObject *args)
{
    PyObject *pyrv;
    const uint8_t *txt_buf;
    uint8_t *bin_buf;
    size_t txt_len, bin_len;
    int status;

    // Strictly validate, we only accept well-formed IDs:
    if (!PyArg_ParseTuple(args, "s:db32dec", &txt_buf)) {
        return NULL;
    }
    txt_len = strlen(txt_buf);
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
    if ((pyrv=PyBytes_FromStringAndSize(NULL, bin_len)) == NULL) {
        return NULL;
    }
    bin_buf = (uint8_t *)PyBytes_AS_STRING(pyrv);

    // decode_x() returns -1 on success:
    status = decode_x(
        txt_len, txt_buf, bin_len, bin_buf,
        DB32_REVERSE, DB32_START, DB32_END
    );
    if (status != -1) {
        if (status >= 0) {
            PyErr_Format(PyExc_ValueError,
                "invalid base32 letter: %c", status
            );
        }
        else {
            PyErr_SetString(PyExc_RuntimeError, "something went very wrong");
        }
        Py_DECREF(pyrv);
        return NULL;
    }
    return pyrv;
}


/* module init */
static struct PyMethodDef dbase32_functions[] = {
    {"db32enc_c", dbase32_db32enc, METH_VARARGS, "db32enc(data)"},
    {"db32dec_c", dbase32_db32dec, METH_VARARGS, "db32dec(text)"},
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
