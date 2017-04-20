// Copyright 2016 SAS Project Authors. All Rights Reserved.
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

#include "itm.h"
#include <Python.h>

#include <iostream>

static PyObject* itm_point_to_point(PyObject* self, PyObject* args) {
  PyObject* elev_obj = NULL;
  double tht_m, rht_m;
  double eps_dielect, sgm_conductivity, eno_ns_surfref;
  double frq_mhz;
  int radio_climate, pol;
  double conf, rel;
  if (!PyArg_ParseTuple(args, "Oddddddiidd:point_to_point",
                        &elev_obj, &tht_m, &rht_m, &eps_dielect, &sgm_conductivity, &eno_ns_surfref,
                        &frq_mhz, &radio_climate, &pol, &conf, &rel)) {
    return NULL;
  }

  if (!PyList_Check(elev_obj)) {
    return NULL;
  }

  Py_ssize_t size = PyList_Size(elev_obj);
  double* elev = new double[size];
  for (Py_ssize_t i = 0; i < size; i++) {
    PyObject* i_obj = PyList_GetItem(elev_obj, i);
    double elev_val = PyFloat_AsDouble(i_obj);
    if (PyErr_Occurred()) {
      delete[] elev;
      return NULL;
    }
    elev[i] = elev_val;
  }

  elev[0] = size-3;
  double dbloss;
  char strmode[100];
  int errnum;
  point_to_point(elev, tht_m, rht_m, eps_dielect, sgm_conductivity, eno_ns_surfref,
                 frq_mhz, radio_climate, pol, conf, rel,
                 dbloss, strmode, errnum);
  delete[] elev;

  return Py_BuildValue("dis", dbloss, errnum, strmode);
}

static PyObject* itm_point_to_point_stat(PyObject* self, PyObject* args) {
  PyObject* elev_obj = NULL;
  double tht_m, rht_m;
  double eps_dielect, sgm_conductivity, eno_ns_surfref;
  double frq_mhz;
  int radio_climate, pol;
  double conf;
  PyObject* rel_obj = NULL;
  int num_rel;
  if (!PyArg_ParseTuple(args, "OddddddiidOi:point_to_point",
                        &elev_obj, &tht_m, &rht_m, &eps_dielect, &sgm_conductivity, &eno_ns_surfref,
                        &frq_mhz, &radio_climate, &pol, &conf, &rel_obj, &num_rel)) {
    return NULL;
  }

  if (!PyList_Check(elev_obj)) {
    return NULL;
  }
 
  if (!PyList_Check(rel_obj)) {
    return NULL;
  }

  Py_ssize_t size = PyList_Size(elev_obj);
  double* elev = new double[size];
  for (Py_ssize_t i = 0; i < size; i++) {
    PyObject* i_obj = PyList_GetItem(elev_obj, i);
    double elev_val = PyFloat_AsDouble(i_obj);
    if (PyErr_Occurred()) {
      delete[] elev;
      return NULL;
    }
    elev[i] = elev_val;
  }
  elev[0] = size-3;

  size = PyList_Size(rel_obj);
  double* rel = new double[size];
  for (Py_ssize_t i = 0; i < size; i++) {
    PyObject* i_obj = PyList_GetItem(rel_obj, i);
    double rel_val = PyFloat_AsDouble(i_obj);
    if (PyErr_Occurred()) {
      delete[] rel;
      return NULL;
    }
    rel[i] = rel_val;
  }

  double* dbloss = new double[size];
  char strmode[100];
  int errnum;
  point_to_pointSTAT(elev, tht_m, rht_m, eps_dielect, sgm_conductivity, eno_ns_surfref,
                     frq_mhz, radio_climate, pol, conf, rel, num_rel,
                     dbloss, strmode, errnum);
  delete[] elev;
  delete[] rel;

  PyObject* loss = PyList_New(num_rel);
  for (int i = 0; i < num_rel; i++) {
    PyList_SetItem(loss, i, Py_BuildValue("d", dbloss[i]));
  }
  
  delete[] dbloss;

  return Py_BuildValue("Ois", loss, errnum, strmode);
}

static PyMethodDef ITMMethods[] = {
  {"point_to_point", itm_point_to_point, METH_VARARGS, "Point-to-point model"},
  {"point_to_point_stat", itm_point_to_point_stat, METH_VARARGS, "Point-to-point model (stats)"},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC inititm(void) {
  Py_InitModule3("itm", ITMMethods, "Longley-Rice ITM Propagation Module");
}

