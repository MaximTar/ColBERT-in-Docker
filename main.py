import math
import os
from functools import lru_cache

from colbert import Indexer, Searcher
from colbert.data import Collection
from colbert.infra import Run, RunConfig, ColBERTConfig
from flask import Flask, request, jsonify

# Environment variables for index configuration
INDEX_NAME = os.getenv("INDEX_NAME", "index")
INDEX_ROOT = os.getenv("INDEX_ROOT", "/app/experiments/{index_name}/indexes")

# Dictionary to store Searcher instances for different indexes
searchers = dict()
app = Flask(__name__)
# Ensure JSON responses support Unicode
app.config["JSON_AS_ASCII"] = False


@app.route("/init_searchers", methods=["POST"])
def init_searchers():
    """
    Initializes searcher instances for TSV files in the data directory.

    This function scans the "/app/data" directory for files with a ".tsv" extension.
    For each TSV file found, it creates a `Searcher` instance using the file's name
    (without the extension) as the index name.
    The searcher is then stored in the `searchers` dictionary with the index name as the key.
    The function returns an HTTP response indicating successful initialization.

    Returns:
        tuple: A tuple containing a string "OK" and an HTTP status code 200.
    """

    for file in os.listdir("/app/data"):
        if file.endswith(".tsv"):
            index_name = file.split(".")[0]
            index_root = INDEX_ROOT.format(index_name=index_name)
            searchers[index_name] = Searcher(
                index=INDEX_NAME, index_root=index_root, collection=f"./data/{file}"
            )
    return "OK", 200


@lru_cache(maxsize=1000000)
def search_query(query, k, index_name):

    """
    search_query(query, k, index_name)

    Searches for the top-k relevant documents for a given query within a specified index.

    Args:
        query (str): The search query string.
        k (int or None): The number of top results to return.
                         If None, defaults to 10. Maximum allowed value is 100.
        index_name (str): The name of the index to search within.

    Returns:
        Response: A Flask JSON response containing the query and a list of top-k results,
                  each with text, pid, rank, score, and probability.
                  If an error occurs, returns a JSON response with an error message and a 400 status code.

    Raises:
        TypeError: If `k` is not an integer or None.
        ValueError: If `k` cannot be converted to an integer.
        KeyError: If `index_name` is not found in the searchers dictionary.
    """

    try:
        # Limit k to max 100
        k = 10 if k is None else min(int(k), 100)
    except (TypeError, ValueError):
        return jsonify({"error": "Bad k"}), 400
    try:
        pids, ranks, scores = searchers[index_name].search(query, k=k)
        # Convert scores to probabilities
        probs = [math.exp(score) for score in scores]
        # Normalize probabilities
        probs = [prob / sum(probs) for prob in probs]
        top_k = [
            {
                "text": searchers[index_name].collection[pid],
                "pid": pid,
                "rank": rank,
                "score": score,
                "prob": prob,
            }
            for pid, rank, score, prob in zip(pids, ranks, scores, probs)
        ]
        # Sort by score (descending) and pid
        top_k.sort(key=lambda p: (-p["score"], p["pid"]))
        return jsonify({"query": query, "topk": top_k})
    except KeyError:
        return jsonify({"error": "Bad index_name"}), 400


@app.route("/api/search/<idx_name>", methods=["GET"])
def search(idx_name):
    """
    Search for documents in the specified index.

    Args:
        idx_name (str): The name of the index to search within.

    Returns:
        Response: A Flask response object containing the search results.

    Notes:
        This endpoint expects a GET request with query parameters:
        - `query`: The search query string.
        - `k`: The number of top results to return.
    """

    return search_query(request.args.get("query"), request.args.get("k"), idx_name)


@app.route("/api/index/<idx_name>", methods=["POST"])
def index(idx_name):
    """
    Args:
        idx_name (str): The name of the index to be created.

    Returns:
        tuple: A tuple containing a response message and an HTTP status code.
               Returns ("OK", 200) if the indexing is successful, or a JSON
               object with an error message and a 500 status code if an
               exception occurs.

    Raises:
        Exception: If an error occurs during the indexing process, an exception
                   is caught and its message is returned in the response.

    This function handles POST requests to create an index for a specified
    collection. It uses the ColBERT indexing framework to index documents
    from a TSV file located at "/app/data/{idx_name}.tsv". The function
    initializes a Run context with a specified configuration and uses an
    Indexer to perform the indexing operation. If the process is successful,
    it returns an "OK" message with a 200 status code. If an error occurs,
    it returns a JSON response with the error message and a 500 status code.
    """

    try:
        with Run().context(RunConfig(nranks=1, experiment=idx_name)):
            collection = Collection(path=f"/app/data/{idx_name}.tsv")
            config = ColBERTConfig(doc_maxlen=300, nbits=2)
            indexer = Indexer(checkpoint="/app/checkpoint", config=config)
            indexer.index(name=INDEX_NAME, collection=collection, overwrite=True)
        return "OK", 200
    except Exception as e:
        return jsonify({"error": repr(e)}), 500
