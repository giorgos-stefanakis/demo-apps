{{- define "demo.labels" -}}
app.kubernetes.io/part-of: demo-app
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "demo.image" -}}
{{ .Values.image.repository }}:{{ required "image.tag is required" .Values.image.tag }}
{{- end }}

{{- define "demo.podLabels" -}}
{{- if .Values.workloadIdentity.clientId }}
azure.workload.identity/use: "true"
{{- end }}
{{- end }}

{{/* Environment shared by api and worker. */}}
{{- define "demo.env" -}}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: demo-db-app
      key: uri
- name: RABBITMQ_URL
  valueFrom:
    secretKeyRef:
      name: demo-mq-default-user
      key: connection_string
- name: OBJECT_STORE_TYPE
  value: {{ .Values.objectStore.type | quote }}
{{- if eq .Values.objectStore.type "s3" }}
- name: S3_ENDPOINT
  value: {{ required "objectStore.s3.endpoint is required" .Values.objectStore.s3.endpoint | quote }}
- name: S3_BUCKET
  value: {{ required "objectStore.s3.bucket is required" .Values.objectStore.s3.bucket | quote }}
- name: AWS_ACCESS_KEY_ID
  valueFrom:
    secretKeyRef:
      name: object-store-s3
      key: access_key_id
- name: AWS_SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: object-store-s3
      key: secret_access_key
{{- else if eq .Values.objectStore.type "azureblob" }}
- name: AZURE_BLOB_ACCOUNT_URL
  value: {{ required "objectStore.azureblob.accountUrl is required" .Values.objectStore.azureblob.accountUrl | quote }}
- name: AZURE_BLOB_CONTAINER
  value: {{ required "objectStore.azureblob.container is required" .Values.objectStore.azureblob.container | quote }}
{{- else }}
{{- fail (printf "objectStore.type %q is not s3 or azureblob" .Values.objectStore.type) }}
{{- end }}
- name: AUTH_TENANT_ID
  value: {{ required "auth.tenantId is required" .Values.auth.tenantId | quote }}
- name: AUTH_CLIENT_ID
  value: {{ required "auth.clientId is required" .Values.auth.clientId | quote }}
- name: AUTH_API_AUDIENCE
  value: {{ required "auth.apiAudience is required" .Values.auth.apiAudience | quote }}
- name: DEMO_API_KEY
  valueFrom:
    secretKeyRef:
      name: demo-api-key
      key: value
{{- end }}
