{{- define "orders-project.name" -}}
{{- .Chart.Name -}}
{{- end }}

{{- define "orders-project.fullname" -}}
{{- if .Values.global.fullnameOverride -}}
{{- .Values.global.fullnameOverride | quote -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end }}


{{- define "orders-project.labels" -}}
app.kubernetes.io/name: {{ include "orders-project.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

