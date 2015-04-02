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

from .clients import APNSClient, GCMClient

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

from .config import (
    APNSConfig,
    APNSSandboxConfig,
    GCMConfig,
    create_apns_config,
    create_apns_sandbox_config,
    create_gcm_config
)
