import os

from behave import *

from util import getRandomLatLongInPolygon, json_load

use_step_matcher("re")


@given("CBSD has obtained a cbsdId = C inside a GWPZ")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    # Load GWPZ Record
    gwpz = json_load(
        os.path.join('testcases', 'testdata', 'gwpz_record_0.json'))
    # Load CBSD info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    # Change device location to be inside GWPZ
    device_a['installationParam']['latitude'], \
    device_a['installationParam']['longitude'] = getRandomLatLongInPolygon(gwpz)
    # # Register device
    cbsd_ids = context.sas_test_case.assertRegistered([device_a])


@step("there is no available channel in the frequency range sent in the inquiredSpectrum parameter")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(
        u'STEP: And there is no available channel in the frequency range sent in the inquiredSpectrum parameter')


@step("CPAS has been triggered to simulate coordination and synchronization tasks")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(u'STEP: And CPAS has been triggered to simulate coordination and synchronization tasks')


@step("Frequency range in the inquiredSpectrum parameter is set to FR")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(u'STEP: And Frequency range in the inquiredSpectrum parameter is set to FR')


@when("DP Test Harness sends a spectrumInquiryRequest message to SAS UU")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(u'STEP: When DP Test Harness sends a spectrumInquiryRequest message to SAS UU')


@then("SAS response includes cbsdId = C\.")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(u'STEP: Then SAS response includes cbsdId = C.')


@step("availableChannel has zero elements")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(u'STEP: And availableChannel has zero elements')


@step("responseCode = 0")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    raise NotImplementedError(u'STEP: And responseCode = 0')
