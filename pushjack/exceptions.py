# -*- coding: utf-8 -*-
"""Exceptions module.
"""

from ._compat import iteritems


__all__ = (
    'APNSError',
    'APNSAuthError',
    'APNSServerError',
    'APNSProcessingError',
    'APNSMissingTokenError',
    'APNSMissingTopicError',
    'APNSMissingPayloadError',
    'APNSInvalidTokenSizeError',
    'APNSInvalidTopicSizeError',
    'APNSInvalidPayloadSizeError',
    'APNSInvalidTokenError',
    'APNSSendError',
    'APNSShutdownError',
    'APNSUnknownError',
    'GCMError',
    'GCMAuthError',
    'GCMServerError',
    'GCMMissingRegistrationError',
    'GCMInvalidRegistrationError',
    'GCMUnregisteredDeviceError',
    'GCMInvalidPackageNameError',
    'GCMMismatchedSenderError',
    'GCMMessageTooBigError',
    'GCMInvalidDataKeyError',
    'GCMInvalidTimeToLiveError',
    'GCMTimeoutError',
    'GCMInternalServerError',
    'GCMDeviceMessageRateExceededError',
    'NotificationError',
    'ServerError',
)


class NotificationError(Exception):
    """Base exception for all notification errors."""
    code = None
    description = None


class ServerError(NotificationError):
    """Base exception for server errors."""
    def __init__(self, identifier):
        super(ServerError, self).__init__(self.code,
                                          self.description,
                                          identifier)
        self.identifier = identifier

    def __str__(self):  # pragma: no cover
        return '{0} (code={1}): {2} for identifier {3}'.format(
            self.__class__.__name__,
            self.code,
            self.description,
            self.identifier)

    def __repr__(self):  # pragma: no cover
        return str(self)


class GCMError(NotificationError):
    """Base exception for GCM errors."""
    pass


class GCMAuthError(GCMError):
    """Exception for error with GCM API key."""
    pass


class GCMServerError(ServerError):
    """Base exception for GCM Server errors."""
    pass


class GCMMissingRegistrationError(GCMServerError):
    """Exception for missing registration ID."""
    code = 'MissingRegistration'
    description = 'Missing registration ID'


class GCMInvalidRegistrationError(GCMServerError):
    """Exception for invalid registration ID"""
    code = 'InvalidRegistration'
    description = 'Invalid registration ID'


class GCMUnregisteredDeviceError(GCMServerError):
    """Exception for unregistered device."""
    code = 'NotRegistered'
    description = 'Device not registered'


class GCMInvalidPackageNameError(GCMServerError):
    """Exception for invalid package name."""
    code = 'InvalidPackageName'
    description = 'Invalid package name'


class GCMMismatchedSenderError(GCMServerError):
    """Exception for mismatched sender."""
    code = 'MismatchSenderId'
    description = 'Mismatched sender ID'


class GCMMessageTooBigError(GCMServerError):
    """Exception for message too big."""
    code = 'MessageTooBig'
    description = 'Message too big'


class GCMInvalidDataKeyError(GCMServerError):
    """Exception for invalid data key."""
    code = 'InvalidDataKey'
    description = 'Invalid data key'


class GCMInvalidTimeToLiveError(GCMServerError):
    """Exception for invalid time to live."""
    code = 'InvalidTtl'
    description = 'Invalid time to live'


class GCMTimeoutError(GCMServerError):
    """Exception for server timeout."""
    code = 'Unavailable'
    description = 'Timeout'


class GCMInternalServerError(GCMServerError):
    """Exception for internal server error."""
    code = 'InternalServerError'
    description = 'Internal server error'


class GCMDeviceMessageRateExceededError(GCMServerError):
    """Exception for device message rate exceeded."""
    code = 'DeviceMessageRateExceeded'
    description = 'Device message rate exceeded'


class APNSError(NotificationError):
    """Base exception for APNS errors."""
    pass


class APNSAuthError(APNSError):
    """Exception with APNS certificate."""
    pass


class APNSServerError(ServerError):
    """Base exception for APNS Server errors."""
    pass


class APNSProcessingError(APNSServerError):
    """Exception for APNS processing error."""
    code = 1
    description = 'Processing error'


class APNSMissingTokenError(APNSServerError):
    """Exception for APNS missing token error."""
    code = 2
    description = 'Missing token'


class APNSMissingTopicError(APNSServerError):
    """Exception for APNS missing topic error."""
    code = 3
    description = 'Missing topic'


class APNSMissingPayloadError(APNSServerError):
    """Exception for APNS payload error."""
    code = 4
    description = 'Missing payload'


class APNSInvalidTokenSizeError(APNSServerError):
    """Exception for APNS invalid token size error."""
    code = 5
    description = 'Invalid token size'


class APNSInvalidTopicSizeError(APNSServerError):
    """Exception for APNS invalid topic size error."""
    code = 6
    description = 'Invalid topic size'


class APNSInvalidPayloadSizeError(APNSServerError):
    """Exception for APNS invalid payload size error."""
    code = 7
    description = 'Invalid payload size'


class APNSInvalidTokenError(APNSServerError):
    """Exception for APNS invalid token error."""
    code = 8
    description = 'Invalid token'


class APNSShutdownError(APNSServerError):
    """Exception for APNS shutdown error."""
    code = 10
    description = 'Shutdown'


class APNSUnknownError(APNSServerError):
    """Exception for APNS unknown error."""
    code = 255
    description = 'Unknown'


class APNSSendError(APNSError):
    """Exception for errors from bulk sending.

    Attributes:
        tokens (list): List of all tokens sent during bulk sending.
        errors (list): List of APNS exceptions for each failed token.
        failures (list): List of all failed tokens.
        successes (list): List of all successful tokens.
        token_errors (dict): Dict mapping the failed tokens to their respective
            APNS exception.
    """
    def __init__(self, message, errors, tokens):
        super(APNSSendError, self).__init__(message)
        self.tokens = tokens
        self.errors = errors
        self.failures = []
        self.successes = []
        self.token_errors = {}

        for err in errors:
            token = tokens[err.identifier]
            self.failures.append(token)
            self.token_errors[token] = err

        self.successes = [token for token in tokens
                          if token not in self.failures]


class Raiser(object):
    """Helper class for raising an exception based on error class name prefix
    and exception code.
    """
    prefix = None
    fallback_exception = None

    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, code, identifier):
        if code not in self.mapping:  # pragma: no cover
            # pylint: disable=not-callable
            raise self.fallback_exception(identifier)

        raise self.mapping[code](identifier)


class GCMServerRaiser(Raiser):
    """Exception raiser classs for GCM server errors."""
    prefix = 'GCM'
    fallback_exception = GCMServerError


class APNSServerRasier(Raiser):
    """Exception raiser class for APNS errors."""
    prefix = 'APNS'
    fallback_exception = APNSUnknownError


def map_errors(prefix):
    mapping = {}
    for name, obj in iteritems(globals()):
        if (name.startswith(prefix) and
                getattr(obj, 'code', None) is not None):
            mapping[obj.code] = obj
    return mapping


gcm_server_errors = map_errors('GCM')
apns_server_errors = map_errors('APNS')


#: Helper method to raise GCM server errors.
raise_gcm_server_error = GCMServerRaiser(gcm_server_errors)

#: Helper method to raise APNS server errors.
raise_apns_server_error = APNSServerRasier(apns_server_errors)
