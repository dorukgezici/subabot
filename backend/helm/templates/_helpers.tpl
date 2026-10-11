{{- define "subabot.selectorLabels" -}}
app.kubernetes.io/name: subabot
app.kubernetes.io/instance: subabot
{{- end }}

{{- define "subabot.labels" -}}
{{ include "subabot.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | quote }}
{{- end }}
