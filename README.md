# OpenCTI FaviconHash Connector

This connector automatically enriches **Domain-Name** observables using the [favicon-hash.kmsec.uk](https://favicon-hash.kmsec.uk/) API. For each domain it retrieves the favicon’s cryptographic hashes and creates a **File** observable that stores the Murmur, MD5 and SHA-256 hash values.

## Features

- Enriches `Domain-Name` observables on demand or automatically.
- Fetches favicon hashes from `https://favicon-hash.kmsec.uk/api/?url=<domain>`.
- Creates a `File` observable with:
    - `name` = Murmur hash (primary identifier)
    - `hashes.MD5` and `hashes.SHA-256` as returned by the API
    - `description` = “Хэш favicon”
    - `labels` = `["favicon"]`
- Reuses an existing `File` observable if a file with the same Murmur hash already exists, avoiding duplicate entries.
- Supports HTTP/HTTPS proxy and custom CA bundles.
- Designed for OpenCTI 6.x (internal enrichment connector).
## Requirements

- An **OpenCTI** platform instance (accessible via URL and API token).
- Docker Engine (for containerised deployment).
- Outbound HTTPS access to `favicon-hash.kmsec.uk:443`.
## Configuration (Environment Variables)

| Variable                       | Description                                  | Example                                |
| ------------------------------ | -------------------------------------------- | -------------------------------------- |
| `OPENCTI_URL`                  | URL of your OpenCTI instance                 | `http://opencti:8080`                  |
| `OPENCTI_TOKEN`                | OpenCTI API token (required)                 | `2b3f...`                              |
| `CONNECTOR_ID`                 | Unique UUID for this connector               | `00000000-0000-0000-0000-000000000001` |
| `CONNECTOR_NAME`               | Display name in OpenCTI                      | `FaviconHash`                          |
| `CONNECTOR_SCOPE`              | Observable type this connector handles       | `Domain-Name`                          |
| `CONNECTOR_AUTO`               | Enable automatic enrichment (`true`/`false`) | `true`                                 |
| `CONNECTOR_LOG_LEVEL`          | Logging verbosity                            | `info`                                 |
| `CONNECTOR_EXPOSE_METRICS`     | Enable Prometheus metrics endpoint           | `false`                                |
| `FAVICON_HASH_API_URL`         | Favicon hash API endpoint                    | `https://favicon-hash.kmsec.uk/api/`   |
| `FAVICON_HASH_MAX_TLP`         | Maximum TLP level allowed for enrichment     | `TLP:AMBER`                            |
| `FAVICON_HASH_REQUEST_TIMEOUT` | HTTP request timeout (seconds)               | `10`                                   |
| `FAVICON_HASH_DELAY`           | Delay between API calls (seconds)            | `0.5`                                  |


> **Note:** The connector always runs once immediately after startup and then waits for internal enrichment requests from OpenCTI.

## Building the Docker Image

Build the image manually:

```bash
docker build -t connector-favicon-hash:6.4.11 .
```
## Running with Docker Compose

Edit the `docker-compose.yml` file and replace all `ChangeMe` values with your actual configuration. Then start the connector:

```bash
docker-compose up -d
```
### Example `docker-compose.yml`

```yaml
  connector-favicon-hash:
    image: beeintelligence/favicon-hash-6.4.11:latest
    environment:
      - OPENCTI_URL=http://opencti:8080
      - OPENCTI_TOKEN=ChangeMe
      - CONNECTOR_ID=ChangeMe
      - CONNECTOR_NAME=FaviconHash
      - CONNECTOR_SCOPE=Domain-Name
      - CONNECTOR_AUTO=true
      - CONNECTOR_LOG_LEVEL=debug
      - CONNECTOR_EXPOSE_METRICS=false
      - FAVICON_HASH_API_URL=https://favicon-hash.kmsec.uk/api/
      - FAVICON_HASH_MAX_TLP=TLP:GREEN
      - FAVICON_HASH_REQUEST_TIMEOUT=10
      - FAVICON_HASH_DELAY=0.5
    restart: always
    depends_on:
      opencti:
        condition: service_healthy
```

## Running with Docker (standalone)

You can run the connector directly with `docker run` without Docker Compose. This is useful for quick testing or when you prefer to manage containers manually.

```bash
docker run -d \
  --name connector-favicon-hash \
  --restart always \
  -e OPENCTI_URL=http://opencti:8080 \
  -e OPENCTI_TOKEN=your-api-token \
  -e CONNECTOR_ID=$(uuidgen) \
  -e CONNECTOR_NAME=FaviconHash \
  -e CONNECTOR_SCOPE=Domain-Name \
  -e CONNECTOR_AUTO=true \
  -e CONNECTOR_LOG_LEVEL=info \
  -e FAVICON_HASH_API_URL=https://favicon-hash.kmsec.uk/api/ \
  -e FAVICON_HASH_MAX_TLP=TLP:AMBER \
  -e FAVICON_HASH_REQUEST_TIMEOUT=10 \
  -e FAVICON_HASH_DELAY=0.5 \
  opencti/connector-favicon-hash:6.4.11
```

**Explanation of flags:**

- `-d` – Run in detached mode (background).
- `--name` – Assign a name to the container.
- `--restart always` – Automatically restart the container if it stops or the host reboots.
- `-e` – Set each environment variable.
- `-v` – Mount a custom CA certificate file (optional; remove if not needed).

To stop and remove the container:

```bash
docker stop connector-favicon-hash
docker rm connector-favicon-hash
```

To view logs:

```bash
docker logs -f connector-favicon-hash
```

## Deploying in Portainer (when OpenCTI is already running)

Since your OpenCTI instance is already deployed in Portainer, you only need to add the FaviconHash connector as a new stack. You have two options to get the image into Portainer:
#### Option A: Import a pre‑built image (recommended)

1. On any machine with Docker, build and save the image:

```bash
docker build -t opencti/connector-favicon-hash:6.4.11 .
docker save opencti/connector-favicon-hash:6.4.11 | gzip > opencti-connector-favicon-hash.tar.gz
```

2. In Portainer, go to **Images** → **Import**.
3. Upload the `opencti-connector-favicon-hash.tar.gz` file.
4. Afterwards, Paste the content of `docker-compose.yml` (modify the `image:` line if needed), and deploy.

#### Option B: Build the image directly in Portainer

1. In Portainer, go to **Images** → **Build Image**.
2. Upload the `Dockerfile` and the entire `src/` folder, or point to a Git repository containing the connector source.
3. Set the image name and tag: `opencti/connector-favicon-hash:6.4.11`.
4. Click **Build**.
5. Paste the content of `docker-compose.yml` (modify the `image:` line if needed), and deploy.

## Manual Testing (without Docker)

Install dependencies and run the connector locally:

```bash
pip install -r src/requirements.txt
export OPENCTI_URL=http://localhost:8080
export OPENCTI_TOKEN=your_token
python src/main.py
```
## Logging

Logs are printed to stdout. You can view them with:

```bash
docker logs connector-favicon-hash
```

Inside Portainer, open the container’s **Logs** panel.

## Troubleshooting

- **No file created** – Verify that the domain is reachable and has a favicon. The connector logs a warning and skips file creation when the API returns no data.
- **Proxy errors** – Ensure `HTTP_PROXY` and `HTTPS_PROXY` are correctly set and that `NO_PROXY` includes your OpenCTI hostname.
- **Certificate errors** – If you are using a custom CA bundle, verify that the mounted file is valid and that `FAVICON_HASH_CA_BUNDLE` points to the correct path.
- **Duplicate files** – The connector reuses existing files based on the Murmur hash stored in the `name` field. If you see unexpected duplicates, check that the `name` field.
