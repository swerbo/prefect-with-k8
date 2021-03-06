{{/*
  COPIED OVER FROM https://github.com/PrefectHQ/server/blob/master/helm/prefect-server/templates/_helpers.tpl
  Helper templates for prefect-server
  Includes:
    name
    nameField
    matchLabels
    commonLabels
    serviceAccountName
*/}}

{{/*
  imagePullSecret:
    Copied over from https://helm.sh/docs/howto/charts_tips_and_tricks/#creating-image-pull-secrets
*/}}
{{- define "imagePullSecret" }}
{{- printf "{\"auths\": {\"%s\": {\"auth\": \"%s\"}}}" .Values.imageCredentials.registry (printf "%s:%s" .Values.imageCredentials.username .Values.imageCredentials.password | b64enc) | b64enc }}
{{- end }}

{{/*
  prefect-server.name:
    Define a name for the application as {chart-name}
    Name fields are limited to 63 characters by the DNS naming spec
*/}}
{{- define "prefect-server.name" -}}
{{ .Values.nameOverride | default .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}


{{- /*
  prefect-server.nameField(component, [namePrefix], [nameSuffix]):
    Populates a configuration name field's value by as {release}-{component}
    Request the component name to be passed by adding to the context e.g.
      include "prefect-server.nameField (merge (dict "component" "apollo") .)
    Also allows prefix and suffix values to be passed
    Name fields are limited to 63 characters by the DNS naming spec
*/}}
{{- define "prefect-server.nameField" -}}
{{- $name := print (.namePrefix | default "") ( .component ) (.nameSuffix | default "") -}}
{{ printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{/*
  prefect-server.matchLabels:
    Provides K8s selection labels typically for use within the `spec` section
    Includes "name" and "instance"
    "component" is not provided and should be added by the component
*/}}
{{- define "prefect-server.matchLabels" -}}
app.kubernetes.io/name: {{ include "prefect-server.name" . }}
app.kubernetes.io/instance:  {{ .Release.Name }}
{{- end -}}
{{/*
  prefect-server.commonLabels:
    Provides common K8s labels, including "prefect-server.matchLabels"
    typically for use within the top-level metadata
    Includes "chart", "version", and "managed-by" as well as the match 
    labels generated by "prefect-server.matchLabels"
    "component" is not provided and should be added by the component
*/}}
{{- define "prefect-server.commonLabels" -}}
{{ include "prefect-server.matchLabels" . }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
{{/*
  prefect-server.serviceAccountName: 
    Create the name of the service account to use
*/}}
{{- define "prefect-server.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{- $createName := include "prefect-server.nameField" (merge (dict "component" "serviceaccount") .) -}}
    {{- .Values.serviceAccount.name | default $createName -}}
{{- else -}}
    {{- .Values.serviceAccount.name | default "default" -}}
{{- end -}}
{{- end -}}
{{/*
  env-unrap: 
    Converts a nested dictionary with keys `prefix` and `map`
    into a list of environment variable definitions, where each
    variable name is an uppercased concatenation of keys in the map
    starting with the original prefix and descending to each leaf.
    The variable value is then the quoted value of each leaf key.
*/}}
{{- define "env-unwrap" -}}
{{- $prefix := .prefix -}}
{{/* Iterate through all keys in the current map level */}}
{{- range $key, $val := .map -}}
{{- $key := upper $key -}}
{{/* Create an environment variable if this is a leaf */}}
{{- if ne (typeOf $val | toString) "map[string]interface {}" }}
- name: {{ printf "%s__%s" $prefix $key }}
  value: {{ $val | quote }}
{{/* Otherwise, recurse into each child key with an updated prefix */}}
{{- else -}}
{{- $prefix := (printf "%s__%s" $prefix $key) -}}
{{- $args := (dict "prefix" $prefix "map" $val)  -}}
{{- include "env-unwrap" $args -}}
{{- end -}}
{{- end -}}
{{- end -}}