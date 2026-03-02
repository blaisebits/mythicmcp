# Contract: Arachne YAML Parameter Schema

Defines the corrected parameter schemas for the 3 fixed commands plus metadata.

## download

```yaml
- name: download
  description: "Download a file from an Arachne webshell callback"
  mythic_command: download
  timeout: 120
  parameters:
    - name: file_path
      type: string
      description: "Path to file to download"
      required: true
```

## upload

```yaml
- name: upload
  description: "Upload a file to an Arachne webshell callback. Use file_id from core_upload_file for the file parameter."
  mythic_command: upload
  timeout: 120
  parameters:
    - name: remote_path
      type: string
      description: "Destination path on target"
      required: true
    - name: file
      type: string
      description: "file_id from core_upload_file for the file to upload"
      required: true
```

## execute_assembly

```yaml
- name: execute_assembly
  description: "Execute a .NET assembly on an Arachne ASPX webshell (Windows/ASPX only). Use file_id from core_upload_file for the file parameter."
  mythic_command: execute_assembly
  timeout: 120
  parameters:
    - name: file
      type: string
      description: "file_id from core_upload_file containing the .NET assembly"
      required: true
    - name: arguments
      type: string
      description: "Arguments to pass to assembly"
      default: ""
```

## cd (description update)

```yaml
- name: cd
  description: "Change working directory on an Arachne webshell (Windows only)"
  mythic_command: cd
  timeout: 60
  parameters:
    - name: path
      type: string
      description: "Path to change to"
      required: true
```

## metadata

```yaml
metadata:
  agent_version: "0.0.4"
```
