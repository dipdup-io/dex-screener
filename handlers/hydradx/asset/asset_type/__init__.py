from scalecodec.exceptions import RemainingScaleBytesNotEmptyException  # type: ignore[import-untyped]

DipDupEventDataCollectPayloadUnhandledError = (RemainingScaleBytesNotEmptyException, NotImplementedError, ValueError)
