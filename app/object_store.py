from typing import Protocol

import boto3
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient
from botocore.config import Config

from app.settings import Settings


class ObjectStore(Protocol):
    def put(self, key: str, data: bytes) -> None: ...

    def get(self, key: str) -> bytes: ...


class S3ObjectStore:
    """S3 API with keys from the environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)."""

    def __init__(self, endpoint: str, bucket: str) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name="us-east-1",
            config=Config(s3={"addressing_style": "path"}),
        )

    def put(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data)

    def get(self, key: str) -> bytes:
        return self._client.get_object(Bucket=self._bucket, Key=key)["Body"].read()


class AzureBlobObjectStore:
    """Azure Blob Storage with the pod's workload identity."""

    def __init__(self, account_url: str, container: str) -> None:
        self._container = ContainerClient(account_url, container, credential=DefaultAzureCredential())

    def put(self, key: str, data: bytes) -> None:
        self._container.upload_blob(key, data, overwrite=True)

    def get(self, key: str) -> bytes:
        return self._container.download_blob(key).readall()


def create_object_store(settings: Settings) -> ObjectStore:
    if settings.object_store_type == "s3":
        return S3ObjectStore(settings.s3_endpoint, settings.s3_bucket)
    if settings.object_store_type == "azureblob":
        return AzureBlobObjectStore(settings.azure_blob_account_url, settings.azure_blob_container)
    raise ValueError(f"Unknown object store type: {settings.object_store_type}")
