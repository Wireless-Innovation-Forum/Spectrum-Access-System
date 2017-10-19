# SAS test cases

## Organization

There are currently two versions of the test spec, one with old test IDs and one
with new test IDs.

*   Old spec: WINNF-TS-0061 V0.0.0-r3.0 (11 August 2017, balloted in WG4 at the
    end of August)
*   New spec: WINNF-TS-0061 V1.0.0-r5.0 (15 Sept. 2017, balloted in WG4 at the
    end of September)

As of Sept. 2017, we will focus primarily on development of test cases in the
new spec. To organize this work, we use the following scheme:

*   Code based on test case definitions in the *old* spec will use the old IDs
    and stay in the "old" files (e.g. registration_testcase.py).
*   Code based on the test case definitions in the *new* spec will use the new
    IDs and be placed in "new" files (e.g. WINNF_FT_S_REG_testcase.py).

Once all new test cases in a category (e.g. Registration) are implemented, the
old file with the old test cases will be removed.

When creating a PR, please identify in the title whether it is based on the old
vs. new IDs and test case definitions. All PRs created before Sept. 20 shall be
assumed to use old IDs and definitions.
