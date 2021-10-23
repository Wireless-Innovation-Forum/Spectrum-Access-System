from behave import fixture, use_fixture

import sas
from sas_testcase import SasTestCase


class SasTestCaseModified(SasTestCase):
    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()


@fixture
def sas_test_case(context):
    context.sas_test_case = SasTestCaseModified()
    context.sas_test_case.setUp()
    yield context.sas_test_case


def before_all(context):
    use_fixture(sas_test_case, context)
