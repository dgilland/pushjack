# -*- coding: utf-8 -*-
"""Exceptions module.
"""

from ._compat import iteritems


class NotificationError(Exception):
    """Base exception for all notification errors."""
    code = None
    description = None


class GCMError(NotificationError):
    """Base exception for GCM errors."""
    pass


class APNSError(NotificationError):
    """Base exception for APNS errors."""
    pass


class APNSDataOverflow(APNSError):
    """Exception for APNS data overflow error."""
    pass


class APNSServerError(APNSError):
    """Base exception for APNS Server errors."""
    def __init__(self, identifier):
        self.identifier = identifier
        super(APNSServerError, self).__init__(self.code,
                                              self.description,
                                              identifier)

    def __str__(self):  # pragma: no cover
        return '{0}: {1} for identifier {2}'.format(self.code,
                                                    self.description,
                                                    self.identifier)


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

    def __init__(self):
        self.mapping = {}

        for name, obj in iteritems(globals()):
            if (name.startswith(self.prefix) and
                    getattr(obj, 'code', None) is not None):
                self.mapping[obj.code] = obj

    def __call__(self, code, *args, **kargs):
        if not isinstance(code, int) and not args and not kargs:
            raise APNSServerError(code)  # pragma: no cover

        if code not in self.mapping:  # pragma: no cover
            raise LookupError('No APNS exception for {0}'.format(code))

        raise self.mapping[code](*args, **kargs)


class APNSServerRasier(Raiser):
    """Exception raiser class for APNS errors."""
    prefix = 'APNS'


#: Helper method to raise APNS server errors.
raise_apns_server_error = APNSServerRasier()
