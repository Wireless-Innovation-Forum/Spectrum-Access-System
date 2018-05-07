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

// This file has a test vector for the ITM implementation as slightly
// modified in itm.cpp. The code has been modified to solve some
// compiler warnings and make it more platform independent.
// Build with 'g++ -Wall itm.cpp itm_test.cpp -o itm_test'
// Then the test can be run with './itm_test'

#include <assert.h>
#include <iostream>
#include <math.h>

#include "itm.h"

// Test vectors from qkpflanx.txt

//  QKPFL TEST 1, PATH 2200 (MEASURED MEDIAN LB=133.2 DB)
//  CRYSTAL PALACE TO MURSLEY, ENGLAND
//
//            DISTANCE        77.8 KM
//           FREQUENCY        41.5 MHZ
//     ANTENNA HEIGHTS   143.9     8.5 M
//   EFFECTIVE HEIGHTS   240.5    18.4 M
//    TERRAIN, DELTA H         89. M
//
//  POL=0, EPS=15., SGM=  .005 S/M
//  CLIM=5, NS=314., K= 1.368
//  PROFILE- NP= 156, XI=  .499 KM
//
//     A DOUBLE-HORIZON PATH
//     DIFFRACTION IS THE DOMINANT MODE
//
//  ESTIMATED QUANTILES OF BASIC TRANSMISSION LOSS (DB)
//     FREE SPACE VALUE-  102.6 DB
//
//        RELIA-    WITH CONFIDENCE
//        BILITY     50.0    90.0    10.0
//
//          1.0     128.6   137.6   119.6
//         10.0     132.2   140.8   123.5
//         50.0     135.8   144.3   127.2
//         90.0     138.0   146.5   129.4
//         99.0     139.7   148.4   131.0


//  QKPFL TEST 2, PATH 1979 (MEASURED MEDIAN LB=149.5 DB)
//  CRYSTAL PALACE TO MURSLEY, ENGLAND
//
//            DISTANCE        77.8 KM
//           FREQUENCY       573.3 MHZ
//     ANTENNA HEIGHTS   194.0     9.1 M
//   EFFECTIVE HEIGHTS   292.5    19.0 M
//    TERRAIN, DELTA H         91. M
//
//  POL=0, EPS=15., SGM=  .005 S/M
//  CLIM=5, NS=314., K= 1.368
//  PROFILE- NP= 156, XI=  .499 KM
//
//     A DOUBLE-HORIZON PATH
//     DIFFRACTION IS THE DOMINANT MODE
//
//  ESTIMATED QUANTILES OF BASIC TRANSMISSION LOSS (DB)
//     FREE SPACE VALUE-  125.4 DB
//
//        RELIA-    WITH CONFIDENCE
//        BILITY     50.0    90.0    10.0
//
//          1.0     144.3   154.1   134.4
//         10.0     150.9   159.5   142.3
//         50.0     157.6   165.7   149.4
//         90.0     161.6   169.9   153.3
//         99.0     164.9   173.6   156.2


// distance profile points from qkpfldat.txt
// CRYSTAL PALACE TO MURSLEY, ENGLAND
// elevations:
// 96   84   65   46   46   46   61   41   33   27   23   19   15   15   15
// 15   15   15   15   15   15   15   15   15   17   19   21   23   25   27
// 29   35   46   41   35   30   33   35   37   40   35   30   51   62   76
// 46   46   46   46   46   46   50   56   67  106   83   95  112  137  137
// 76  103  122  122   83   71   61   64   67   71   74   77   79   86   91
// 83   76   68   63   76  107  107  107  119  127  133  135  137  142  148
// 152  152  107  137  104   91   99  120  152  152  137  168  168  122  137
// 137  170  183  183  187  194  201  192  152  152  166  177  198  156  127
// 116  107  104  101   98   95  103   91   97  102  107  107  107  103   98
// 94   91  105  122  122  122  122  122  137  137  137  137  137  137  137
// 137  140  144  147  150  152  159

// QKPFL TEST 1, PATH 2200 (MEASURED MEDIAN LB=133.2 DB)
// 77        41.5      143.9     8.5                 314.

// QKPFL TEST 2, PATH 1979 (MEASURED MEDIAN LB=149.5 DB)
// 77        573.3     194.0     9.1




int main() {

  // Path profile elevations: Crystal Palace to Mursley, England.
  double elev[] = { 156, 77800./156.,
96,   84,   65,   46,   46,   46,   61,   41,   33,   27,   23,   19,   15,   15,   15,
15,   15,   15,   15,   15,   15,   15,   15,   15,   17,   19,   21,   23,   25,   27,
29,   35,   46,   41,   35,   30,   33,   35,   37,   40,   35,   30,   51,   62,   76,
46,   46,   46,   46,   46,   46,   50,   56,   67,  106,   83,   95,  112,  137,  137,
76,  103,  122,  122,   83,   71,   61,   64,   67,   71,   74,   77,   79,   86,   91,
83,   76,   68,   63,   76,  107,  107,  107,  119,  127,  133,  135,  137,  142,  148,
152, 152,  107,  137,  104,   91,   99,  120,  152,  152,  137,  168,  168,  122,  137,
137, 170,  183,  183,  187,  194,  201,  192,  152,  152,  166,  177,  198,  156,  127,
116, 107,  104,  101,   98,   95,  103,   91,   97,  102,  107,  107,  107,  103,   98,
94,   91,  105,  122,  122,  122,  122,  122,  137,  137,  137,  137,  137,  137,  137,
137, 140,  144,  147,  150,  152,  159 };

  double confidence_values[] = { .5, .9, .1 };
  double reliability_values[] = { .01, .1, .5, .9, .99 };

  int n_failure = 0;

  // Path 2200
  std::cout << "==== Path 2200 =====" << std::endl;

  double expected_loss[5][3] = {
    { 128.6, 137.6, 119.6 },
    { 132.2, 140.8, 123.5 },
    { 135.8, 144.3, 127.2 },
    { 138.0, 146.5, 129.4 },
    { 139.7, 148.4, 131.0 } };


  for (int c = 0; c < 3; c++) {
    for (int r = 0; r < 5; r++) {
      double conf = confidence_values[c];
      double rel = reliability_values[r];
      double loss = expected_loss[r][c];

      double dbloss = 0;
      int errnum = -100;
      char strmode[1000];
      double ver0, ver1;

      point_to_point(elev, 143.9, 8.5, 15, .005, 314, 41.5,
                     RADIO_CLIMATE_CONTINENTAL_TEMPERATE, POL_HORIZONTAL,
                     conf, rel, 12, true,
                     dbloss, strmode, errnum, ver0, ver1);

      std::cout << "rel=" << rel << " conf=" << conf << std::endl;
      std::cout << strmode << std::endl;
      std::cout << "loss=" << dbloss << " " << "err=" << errnum << std::endl;
      std::cout << "expected=" << loss << std::endl;
      std::cout << "difference=" << fabs(loss-dbloss) << std::endl;
      if (fabs(loss - dbloss) > 0.05) {
        std::cout << "FAILURE" << std::endl;
        n_failure++;
      }
      std::cout << std::endl;
    }
  }

  // Path 1979
  std::cout << "==== Path 1979 =====" << std::endl;

  double expected_loss_1979[5][3] = {
    { 144.3, 154.1, 134.4 },
    { 150.9, 159.5, 142.3 },
    { 157.6, 165.7, 149.4 },
    { 161.6, 169.9, 153.3 },
    { 164.9, 173.6, 156.2 } };

  for (int c = 0; c < 3; c++) {
    for (int r = 0; r < 5; r++) {
      double conf = confidence_values[c];
      double rel = reliability_values[r];
      double loss = expected_loss_1979[r][c];

      double dbloss = 0;
      int errnum = -100;
      char strmode[1000];
      double ver0, ver1;

      point_to_point(elev, 194.0, 9.1, 15, .005, 314, 573.3,
                     RADIO_CLIMATE_CONTINENTAL_TEMPERATE, POL_HORIZONTAL,
                     conf, rel, 12, true,
                     dbloss, strmode, errnum, ver0, ver1);

      std::cout << "rel=" << rel << " conf=" << conf << std::endl;
      std::cout << strmode << std::endl;
      std::cout << "loss=" << dbloss << " " << "err=" << errnum << std::endl;
      std::cout << "expected=" << loss << std::endl;
      std::cout << "difference=" << fabs(loss-dbloss) << std::endl;
      if (fabs(loss - dbloss) > 0.05) {
        std::cout << "FAILURE" << std::endl;
        n_failure++;
      }
      std::cout << std::endl;
    }
  }
  if (!n_failure) {
    std::cout << "TEST SUCCESS" << std::endl;
  } else {
    std::cout << "FAILED TESTS: " << n_failure << std::endl;
  }
}
