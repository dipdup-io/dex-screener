from scalecodec.exceptions import RemainingScaleBytesNotEmptyException  # type: ignore[import-untyped]

DipDupEventDataCollectPayloadUnhandledError = (RemainingScaleBytesNotEmptyException, NotImplementedError, ValueError)


def validate_framework_exception(exception):
    match exception:
        case NotImplementedError(
            args=(
                'Decoder class for "bounded_collections:bounded_vec:BoundedVec@65" not found'
                | 'Decoder class for "bounded_collections:bounded_vec:BoundedVec@68" not found'
                | 'Decoder class for "bounded_collections:bounded_vec:BoundedVec@70" not found'
                | 'Decoder class for "bounded_collections:bounded_vec:BoundedVec@193" not found'
                | 'Decoder class for "bounded_collections:bounded_vec:BoundedVec@194" not found',
            )
        ):
            pass
        case _:
            raise
