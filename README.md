# demo-apps

A minimal web app used to test how an application stack deploys onto different Kubernetes clusters. It is a demo, not
a product.

- `api` (FastAPI): serves a static page, validates Entra ID tokens, takes file uploads, streams a fake chat reply over
  server-sent events.
- `worker`: consumes upload messages from RabbitMQ, reads the file from object storage and writes a row to PostgreSQL.

Both run from one image. Object storage is S3 or Azure Blob, chosen by configuration.

## Layout

```
app/        Python source for api and worker; static/ holds the page
chart/      Helm chart: the two Deployments, the PostgreSQL and RabbitMQ resources, routing, secrets
scripts/    smoke test
```

## Endpoints

| Path | Auth | Does |
|---|---|---|
| `GET /` | none | The page: sign-in, upload, file list, chat |
| `GET /config.json` | none | Sign-in settings for the page |
| `GET /healthz` | none | Health, and a fingerprint of `demo-api-key` that shows the secret arrived |
| `POST /upload` | token | Stores the file and publishes a message to the `uploads` queue |
| `GET /files` | token | Files the worker has stored |
| `GET /chat` | token | A canned reply, streamed one token at a time |

## Chart values

The chart sees the cluster only through these values. Each cluster sets them:

| Value | Meaning |
|---|---|
| `routing` | `gateway-api` with a Gateway `parentRef`, or `ingress` with a class, annotations and an optional TLS secret |
| `storageClassName` | Volumes of PostgreSQL and RabbitMQ |
| `objectStore` | `s3` (endpoint, bucket; keys from the secret store) or `azureblob` (account URL, container) |
| `secretStore` | The External Secrets Operator store. `property` picks a field when the backend stores maps |
| `workloadIdentity.clientId` | Azure identity of the pods; empty when not on Azure |

The chart expects these from the cluster: the CloudNativePG and RabbitMQ Cluster operators, External Secrets Operator,
a `demo-api-key` entry in the secret store and, for `s3`, an `object-store` entry with `access_key_id` and
`secret_access_key`. The namespace is `demo`; the service accounts are `api` and `worker`.

`auth` holds the tenant ID, client ID and API audience of the Entra ID app registration.

## Build

```sh
make push                                # build, then load into the kind cluster
make push REGISTRY=<name>.azurecr.io     # also push to the registry
```

The image tag is the short commit hash. Set `IMAGE_TAG` to override it.

## Check

```sh
make lint                       # ruff and helm lint
make smoke                      # health, config and 401 through http://localhost
TOKEN=<access token> make smoke # also upload and the chat stream
```

Set `BASE_URL` to check another host.
