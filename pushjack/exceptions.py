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
        return '{0}: {1} for identifier {2}'.format(self.code,
                                                    self.description,
                                                    self.identifier)


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


class Raiser(object):
    """Helper class for raising an exception based on error class name prefix
    and exception code.
    """
    prefix = None
    base_exception = None

    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, code, *args, **kargs):
        if not isinstance(code, int) and not args and not kargs:
            # pylint: disable=not-callable
            raise self.base_exception(code)  # pragma: no cover

        if code not in self.mapping:  # pragma: no cover
            raise LookupError('No server exception for {0}'.format(code))

        raise self.mapping[code](*args, **kargs)


class GCMServerRaiser(Raiser):
    """Exception raiser classs for GCM server errors."""
    prefix = 'GCM'
    base_exception = GCMServerError


class APNSServerRasier(Raiser):
    """Exception raiser class for APNS errors."""
    prefix = 'APNS'
    base_exception = APNSServerError


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
