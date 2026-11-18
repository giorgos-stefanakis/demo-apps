import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str
    rabbitmq_url: str
    object_store_type: str
    s3_endpoint: str
    s3_bucket: str
    azure_blob_account_url: str
    azure_blob_container: str
    auth_tenant_id: str
    auth_client_id: str
    auth_api_audience: str
    demo_api_key: str

    @classmethod
    def from_env(cls) -> Settings:
        object_store_type = _required("OBJECT_STORE_TYPE")
        return cls(
            database_url=_required("DATABASE_URL"),
            rabbitmq_url=_required("RABBITMQ_URL"),
            object_store_type=object_store_type,
            s3_endpoint=_required("S3_ENDPOINT") if object_store_type == "s3" else "",
            s3_bucket=_required("S3_BUCKET") if object_store_type == "s3" else "",
            azure_blob_account_url=_required("AZURE_BLOB_ACCOUNT_URL") if object_store_type == "azureblob" else "",
            azure_blob_container=_required("AZURE_BLOB_CONTAINER") if object_store_type == "azureblob" else "",
            auth_tenant_id=_required("AUTH_TENANT_ID"),
            auth_client_id=_required("AUTH_CLIENT_ID"),
            auth_api_audience=_required("AUTH_API_AUDIENCE"),
            demo_api_key=_required("DEMO_API_KEY"),
        )
