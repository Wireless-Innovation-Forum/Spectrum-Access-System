// Copyright 2017 SAS Project Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <Python.h>
#include <iostream>

#include "its/ehata.h"

static PyObject* ExtendedHata(PyObject* self, PyObject* args) {
  PyObject* elev_obj = NULL;
  double frq_mhz;
  double hb_m;
  double hm_m;
  int environment;
  if (!PyArg_ParseTuple(args, "Odddi:ehata_its_ExtendedHata",
                        &elev_obj, &frq_mhz, &hb_m, &hm_m, &environment)) {
    return NULL;
  }

  if (!PyList_Check(elev_obj)) {
    return NULL;
  }
  Py_ssize_t size = PyList_Size(elev_obj);
  if (size < 4) {
    PyErr_SetString(PyExc_ValueError, "Invalid profile size. Should be >= 4.");
    return NULL;
  }
  // Build reverse profile from Rx to Tx, as it is the convention
  // for E-Hata C++ module.
  double* elev = new double[size];
  PyObject *obj = PyList_GetItem(elev_obj, 0);
  elev[0] = PyFloat_AsDouble(obj);
  obj = PyList_GetItem(elev_obj, 1);
  elev[1] = PyFloat_AsDouble(obj);
  for (Py_ssize_t i = 2; i < size; i++) {
    PyObject* i_obj = PyList_GetItem(elev_obj, size+1-i);
    elev[i] = PyFloat_AsDouble(i_obj);
  }
  if (PyErr_Occurred()) {
    delete[] elev;
    PyErr_SetString(PyExc_ValueError, "Profile should only contain numerical values.");
    return NULL;
  }
  if (elev[0] > size-3) {
    delete[] elev;
    PyErr_SetString(PyExc_ValueError, "Invalid Profile. Size in slot 0 bigger than actual list size.");
    return NULL;
  }

  double dbloss;
  InterValues dbg_vals;
  ExtendedHata_DBG(elev, frq_mhz, hb_m, hm_m, environment,
                   &dbloss, &dbg_vals);
  delete[] elev;

  return Py_BuildValue("d", dbloss);

  // For debug, full data could be returned:
  // return Py_BuildValue("dddddddddddddddddddbddi", dbloss,
  //       	       (double)dbg_vals.d_bp__km,
  //                   (double)dbg_vals.att_1km,
  //                   (double)dbg_vals.att_100km,
  //       	       (double)dbg_vals.h_b_eff__meter,
  //                   (double)dbg_vals.h_m_eff__meter,
  //       	       (double)dbg_vals.pfl10__meter,
  //                   (double)dbg_vals.pfl50__meter,
  //       	       (double)dbg_vals.pfl90__meter,
  //                   (double)dbg_vals.deltah__meter,
  //       	       (double)dbg_vals.d__km,
  //       	       (double)dbg_vals.d_hzn__meter[0],
  //                   (double)dbg_vals.d_hzn__meter[1],
  //       	       (double)dbg_vals.h_avg__meter[0],
  //                   (double)dbg_vals.h_avg__meter[1],
  //       	       (double)dbg_vals.theta_m__mrad,
  //                   (double)dbg_vals.beta,
  //                   (double)dbg_vals.iend_ov_sea,
  //       	       (double)dbg_vals.hedge_tilda,
  //                   dbg_vals.single_horizon,
  //       	       (double)dbg_vals.slope_max,
  //                   (double)dbg_vals.slope_min,
  //                   dbg_vals.trace_code);
}


static PyObject* MedianBasicPropLoss(PyObject* self, PyObject* args) {
  double frq_mhz;
  double hb_m;
  double hm_m;
  double d_km;
  int environment;
  if (!PyArg_ParseTuple(args, "ddddi:ehata_its_ExtendedHata",
                        &frq_mhz, &hb_m, &hm_m, &d_km, &environment)) {
    return NULL;
  }

  double dbloss;
  InterValues dbg_vals;
  MedianBasicPropLoss(frq_mhz, hb_m, hm_m, d_km, environment,
                      &dbloss, &dbg_vals);

  return Py_BuildValue("d", dbloss);

  // For debug, full data could be returned:
  // return Py_BuildValue("ddddi", dbloss,
  //       	       (double)dbg_vals.d_bp__km,
  //                   (double)dbg_vals.att_1km,
  //                   (double)dbg_vals.att_100km,
  //       	       dbg_vals.trace_code);

}

static PyObject* SetWinnForumExtensions(PyObject* self, PyObject* args) {

  PyObject *val = NULL;
  if (!PyArg_ParseTuple(args, "O:ehata_its_SetWinnForumExtensions",
                        &val)) {
    return NULL;
  }
  bool on = PyObject_IsTrue(val);

  SetWinnForumExtensions(on);

  Py_RETURN_NONE;
}


static PyMethodDef EHATAMethods[] = {
  {"ExtendedHata", ExtendedHata, METH_VARARGS, "eHata Point-to-point model"},
  {"MedianBasicPropLoss", MedianBasicPropLoss, METH_VARARGS, "Median Basic propagation loss"},
  {"SetWinnForumExtensions", SetWinnForumExtensions, METH_VARARGS, "Set WinnForum Extensions"},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initehata_its(void) {
  Py_InitModule3("ehata_its", EHATAMethods, "eHata WinnForum Propagation Module");
}
