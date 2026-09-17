from datetime import datetime

from app.base_models.transfer import BaseTransfer, OperationType


class TransferRequest(BaseTransfer):
    pass


class TransferResponse(BaseTransfer):
    made_at: datetime
    operation_type: OperationType
