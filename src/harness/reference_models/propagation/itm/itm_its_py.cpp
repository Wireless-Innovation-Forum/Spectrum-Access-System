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

#include "its/itm.h"
#include <Python.h>

#include <iostream>

static PyObject* itm_point_to_point(PyObject* self, PyObject* args) {
  PyObject* elev_obj = NULL;
  double tht_m, rht_m;
  double eps_dielect, sgm_conductivity, eno_ns_surfref;
  double frq_mhz;
  int radio_climate, pol;
  double conf, rel;
  int mdvar = 12;  // Default arguments
  int eno_final = 0;
  if (!PyArg_ParseTuple(args, "Oddddddiidd|ii:point_to_point",
                        &elev_obj, &tht_m, &rht_m, &eps_dielect, &sgm_conductivity,
                        &eno_ns_surfref,
                        &frq_mhz, &radio_climate, &pol, &conf, &rel, &mdvar, &eno_final)) {
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
  point_to_point(elev, tht_m, rht_m, eps_dielect, sgm_conductivity,
                 eno_ns_surfref, frq_mhz, radio_climate, pol, conf, rel,
                 mdvar, !!eno_final,
                 dbloss, strmode, errnum);
  delete[] elev;
  return Py_BuildValue("dsi", dbloss, strmode, errnum);
}

static PyObject* itm_point_to_point_rels(PyObject* self, PyObject* args) {
  PyObject* elev_obj = NULL;
  double tht_m, rht_m;
  double eps_dielect, sgm_conductivity, eno_ns_surfref;
  double frq_mhz;
  int radio_climate, pol;
  double conf;
  PyObject* rels_obj = NULL;
  int mdvar = 12;  // Default arguments
  int eno_final = 0;
  if (!PyArg_ParseTuple(args, "OddddddiidO|ii:point_to_point_rels",
                        &elev_obj, &tht_m, &rht_m, &eps_dielect, &sgm_conductivity,
                        &eno_ns_surfref,
                        &frq_mhz, &radio_climate, &pol, &conf, &rels_obj,
                        &mdvar, &eno_final)) {
    return NULL;
  }

  if (!PyList_Check(elev_obj)) {
    return NULL;
  }

  if (!PyList_Check(rels_obj)) {
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

  size = PyList_Size(rels_obj);
  double* rels = new double[size];
  for (Py_ssize_t i = 0; i < size; i++) {
    PyObject* rel_obj = PyList_GetItem(rels_obj, i);
    double rel = PyFloat_AsDouble(rel_obj);
    if (PyErr_Occurred()) {
      delete[] rels;
      return NULL;
    }
    rels[i] = rel;
  }
  int num_rels = size;
  double* db_losses = new double[num_rels];
  char strmode[100];
  int errnum;
  point_to_point_rels(elev, tht_m, rht_m, eps_dielect, sgm_conductivity,
                      eno_ns_surfref, frq_mhz, radio_climate, pol, conf,
                      rels, num_rels,
                      mdvar, !!eno_final,
                      db_losses, strmode, errnum);
  delete[] elev;
  delete[] rels;

  PyObject* loss_obj = PyList_New(num_rels);
  for (int k = 0; k < size; k++ ) {
    PyList_SET_ITEM(loss_obj, k, Py_BuildValue("d", db_losses[k]));
  }
  delete[] db_losses;

  return Py_BuildValue("Osi", loss_obj, strmode, errnum);
}

static PyMethodDef ITMMethods[] = {
  {"point_to_point", itm_point_to_point, METH_VARARGS, "Point-to-point model"},
  {"point_to_point_rels", itm_point_to_point_rels, METH_VARARGS, "Point-to-point-Rels model"},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC inititm_its(void) {
  Py_InitModule3("itm_its", ITMMethods, "Longley-Rice ITM Propagation Module");
}
