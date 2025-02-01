# ColBERT in Docker

This repository provides a Dockerized setup for running ColBERT search indexing and querying using Flask. 
The service allows indexing and searching over text collections stored in TSV files.

## Setup

Ensure you have Docker and Docker Compose installed. 
Then, build and start the service with:

```shell
docker-compose up --build
```

## API Endpoints

### Indexing Data

Before initializing searchers, you must index the data.

#### `POST /api/index/<idx_name>`

Indexes documents from a TSV file into ColBERT. 
`<idx_name>` corresponds to a file named `<idx_name>.tsv` located in the `/data` directory.

To index your files, run:
```shell
POST http://localhost:9881/api/index/<idx_name>
```

#### `POST /init_searchers`

Initializes searchers for all indexed datasets. 
Must be called after `/api/index/<idx_name>` has been executed for the relevant dataset.

To initialize searchers, run:
```shell
POST http://localhost:9881/init_searchers
```

### Searching Data

#### `GET /api/search/<idx_name>?query=<query>&k=<k>`

Performs a search query on the indexed dataset specified by `<idx_name>`. 
Returns the top `k` results.

## Folder Structure

- `Dockerfile`: Defines the containerized environment
- `docker-compose.yaml`: Manages the service dependencies
- `app.py`: The Flask API implementation
- `/data`: Directory where TSV files (`<idx_name>.tsv`) are stored for indexing
- `/experiments`: Stores indexed data
- `/checkpoint`: Stores model checkpoints

## Running in Docker

To run the ColBERT service inside Docker:

```sh
docker-compose up --build
```

Ensure that your data files (`<idx_name>.tsv`) are placed inside the `/data` directory before starting the indexing process.

