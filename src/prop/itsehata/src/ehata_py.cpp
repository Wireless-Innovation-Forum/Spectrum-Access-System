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

#include "ehata.h"
#include <Python.h>

#include <iostream>

static PyObject* ehata_point_to_point(PyObject* self, PyObject* args) {
  PyObject* elev_obj = NULL;
  double frq_mhz;
  double hb_m;
  double hm_m;
  int environment;
  if (!PyArg_ParseTuple(args, "Odddi:ehata_point_to_point",
                        &elev_obj, &frq_mhz, &hb_m, &hm_m, &environment)) {
    return NULL;
  }

  if (!PyList_Check(elev_obj)) {
    return NULL;
  }

  Py_ssize_t size = PyList_Size(elev_obj);
  float* elev = new float[size];
  for (Py_ssize_t i = 0; i < size; i++) {
    PyObject* i_obj = PyList_GetItem(elev_obj, i);
    double elev_val = PyFloat_AsDouble(i_obj);
    if (PyErr_Occurred()) {
      delete[] elev;
      return NULL;
    }
    elev[i] = (float)elev_val;
  }

  elev[0] = size-3;
  float dbloss;
  InterValues dbg_vals;
  ExtendedHata_DBG(elev, frq_mhz, hb_m, hm_m, environment,
                   &dbloss, &dbg_vals);
  delete[] elev;

  return Py_BuildValue("dddddddddddddddddddbddi", dbloss,
		       (double)dbg_vals.d_bp__km, (double)dbg_vals.att_1km, (double)dbg_vals.att_100km,
		       (double)dbg_vals.h_b_eff__meter, (double)dbg_vals.h_m_eff__meter,
		       (double)dbg_vals.pfl10__meter, (double)dbg_vals.pfl50__meter,
		       (double)dbg_vals.pfl90__meter, (double)dbg_vals.deltah__meter,
		       (double)dbg_vals.d__km,
		       (double)dbg_vals.d_hzn__meter[0], (double)dbg_vals.d_hzn__meter[1],
		       (double)dbg_vals.h_avg__meter[0], (double)dbg_vals.h_avg__meter[1],
		       (double)dbg_vals.theta_m__mrad, (double)dbg_vals.beta, (double)dbg_vals.iend_ov_sea,
		       (double)dbg_vals.hedge_tilda, dbg_vals.single_horizon,
		       (double)dbg_vals.slope_max, (double)dbg_vals.slope_min, dbg_vals.trace_code);
}

static PyMethodDef EHATAMethods[] = {
  {"point_to_point", ehata_point_to_point, METH_VARARGS, "eHata Point-to-point model"},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initehata(void) {
  Py_InitModule3("ehata", EHATAMethods, "eHata Propagation Module");
}

