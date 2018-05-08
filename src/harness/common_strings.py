"""Strings which are repeated throughout the test code.
"""

EXPECTED_SUCCESSFUL_REGISTRATION = (
    'Registration was expected to succeed and failure to register almost '
    'certainly indicates a configuration error. Please attempt registration of'
    ' the same device using REG.11 and verify that it succeeds.'
)

EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT = (
    'The Registration and Grant requests were expected to succeed and failure'
    ' almost certainly indicates a configuration error. Please attempt the '
    'same requests in GRA.17 and verify that they succeed.')

CONFIG_ERROR_SUSPECTED = (
    'This operation was expected to succeed; failure is almost certainly due '
    'to a configuration error.'
)
