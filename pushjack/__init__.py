# -*- coding: utf-8 -*-
"""Pushjack module.
"""

from .__meta__ import (
    __title__,
    __summary__,
    __url__,
    __version__,
    __author__,
    __email__,
    __license__
)

from .apns import (
    APNSExpiredToken,
)

from .clients import (
    APNSClient,
    GCMClient,
)

from .exceptions import (
    APNSError,
    APNSAuthError,
    APNSServerError,
    APNSProcessingError,
    APNSMissingTokenError,
    APNSMissingTopicError,
    APNSMissingPayloadError,
    APNSInvalidTokenSizeError,
    APNSInvalidTopicSizeError,
    APNSInvalidPayloadSizeError,
    APNSInvalidTokenError,
    APNSSendError,
    APNSShutdownError,
    APNSUnknownError,
    GCMError,
    GCMAuthError,
    GCMServerError,
    GCMMissingRegistrationError,
    GCMInvalidRegistrationError,
    GCMUnregisteredDeviceError,
    GCMInvalidPackageNameError,
    GCMMismatchedSenderError,
    GCMMessageTooBigError,
    GCMInvalidDataKeyError,
    GCMInvalidTimeToLiveError,
    GCMTimeoutError,
    GCMInternalServerError,
    GCMDeviceMessageRateExceededError,
    NotificationError,
    ServerError,
)

from .gcm import (
    GCMCanonicalID,
    GCMResponse,
)

from .config import (
    APNSConfig,
    APNSSandboxConfig,
    GCMConfig,
    create_apns_config,
    create_apns_sandbox_config,
    create_gcm_config
)


# Set default logging handler to avoid "No handler found" warnings.
import logging

try:  # Python 2.7+
    from logging import NullHandler  # pylint: disable=no-name-in-module
except ImportError:  # pragma: no cover
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
