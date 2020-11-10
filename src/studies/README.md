# Studies

Holds various studies and simulation tools.


## Setup

Studies depends in general on the `reference_models` and various `lib` packages.

In order to use them you should:
 - have your PYTHONPATH pointing to the top level `src/harness/` directory
 - have your PYTHONPATH pointing to the top level `src/lib/` directory

## Full installation instructions

You can ignore this section if your Winnforum is alreadys installed/functional.

a. **Create local git repository:**

git clone https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System.git

b. **Setup your PYTHONPATH to have the directories:**

    Spectrum-Access-System/src/harness
    Spectrum-Access-System/src/lib
    
c. **Install all prerequesite:**

See the page https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/README.md 
for a full list of prerequesite and preferred installation method.
Note: some of them might not be required for the scripts and only useful for the test harness
(ssl, cry[tograpjy, pyJWT, ..). Best to install everything and not worry which one are necessary.

d. **Initialize the reference models (geo and propagation models):**

See:
 https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/README.md,
and
 https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/src/harness/reference_models/propagation/README.md

In particular this means:
 - installing the geo terrain data
 - compiling the propagation model modules

e. **Install the specific studies requirements:**

See the dedicated README.md.
