from pydantic import BaseModel


class UploadPresignRequest(BaseModel):
    content_type: str


class UploadPresignResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in: int


class DownloadPresignResponse(BaseModel):
    download_url: str
    expires_in: int

