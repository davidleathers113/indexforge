"""Performance testing script for Weaviate migration."""

from datetime import datetime
import json
import time
from typing import Dict, List

from loguru import logger
import weaviate

from tests.data.weaviate_test_dataset import generate_test_documents, load_test_dataset


class WeaviatePerformanceTest:
    """Performance testing for Weaviate operations."""

    def __init__(
        self,
        client: weaviate.Client,
        class_name: str = "Document",
        batch_size: int = 100,
    ):
        """Initialize performance test.

        Args:
            client: Weaviate client instance
            class_name: Name of the document class
            batch_size: Size of batches for operations
        """
        self.client = client
        self.class_name = class_name
        self.batch_size = batch_size
        self.results: Dict = {}

    def setup_schema(self):
        """Set up test schema in Weaviate."""
        schema = {
            "class": self.class_name,
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "model": "sentence-transformers-all-MiniLM-L6-v2",
                    "poolingStrategy": "mean",
                    "vectorizeClassName": False,
                }
            },
            "properties": [
                {"name": "title", "dataType": ["text"]},
                {"name": "content", "dataType": ["text"]},
                {"name": "file_path", "dataType": ["text"]},
                {"name": "file_type", "dataType": ["text"]},
                {"name": "metadata_json", "dataType": ["text"]},
            ],
        }

        try:
            self.client.schema.create_class(schema)
            logger.info(f"Created schema for class {self.class_name}")
        except Exception as e:
            logger.warning(f"Schema creation failed: {e}")

    def measure_batch_import(self, documents: List[Dict]) -> Dict:
        """Measure batch import performance.

        Args:
            documents: List of documents to import

        Returns:
            Performance metrics
        """
        start_time = time.time()
        total_docs = len(documents)
        successful_imports = 0

        try:
            with self.client.batch as batch:
                batch.configure(batch_size=self.batch_size)
                for doc in documents:
                    # Convert metadata to JSON string
                    doc["metadata_json"] = json.dumps(doc["metadata"])

                    # Add document to batch
                    batch.add_data_object(
                        data_object=doc,
                        class_name=self.class_name,
                    )
                    successful_imports += 1

            duration = time.time() - start_time

            return {
                "operation": "batch_import",
                "total_documents": total_docs,
                "successful_imports": successful_imports,
                "failed_imports": total_docs - successful_imports,
                "duration_seconds": duration,
                "docs_per_second": total_docs / duration if duration > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Batch import failed: {e}")
            return {
                "operation": "batch_import",
                "error": str(e),
                "total_documents": total_docs,
                "successful_imports": successful_imports,
                "failed_imports": total_docs - successful_imports,
            }

    def measure_search_performance(
        self,
        num_queries: int = 100,
        limit: int = 10,
    ) -> Dict:
        """Measure search performance.

        Args:
            num_queries: Number of search queries to perform
            limit: Number of results per query

        Returns:
            Performance metrics
        """
        start_time = time.time()
        successful_queries = 0
        total_results = 0
        query_times = []

        try:
            # Load test documents for random content queries
            test_docs = load_test_dataset()

            for _ in range(num_queries):
                # Select random document for content
                doc = test_docs[_ % len(test_docs)]
                query_start = time.time()

                try:
                    result = (
                        self.client.query.get(
                            self.class_name, ["title", "content", "metadata_json"]
                        )
                        .with_near_text({"concepts": [doc["content"][:100]]})
                        .with_limit(limit)
                        .do()
                    )

                    query_duration = time.time() - query_start
                    query_times.append(query_duration)

                    # Count results
                    results = result.get("data", {}).get("Get", {}).get(self.class_name, [])
                    total_results += len(results)
                    successful_queries += 1

                except Exception as e:
                    logger.error(f"Query failed: {e}")

            duration = time.time() - start_time

            return {
                "operation": "search",
                "total_queries": num_queries,
                "successful_queries": successful_queries,
                "failed_queries": num_queries - successful_queries,
                "total_results": total_results,
                "avg_results_per_query": (
                    total_results / successful_queries if successful_queries > 0 else 0
                ),
                "duration_seconds": duration,
                "queries_per_second": num_queries / duration if duration > 0 else 0,
                "avg_query_time": sum(query_times) / len(query_times) if query_times else 0,
                "min_query_time": min(query_times) if query_times else 0,
                "max_query_time": max(query_times) if query_times else 0,
            }

        except Exception as e:
            logger.error(f"Search performance measurement failed: {e}")
            return {
                "operation": "search",
                "error": str(e),
                "total_queries": num_queries,
                "successful_queries": successful_queries,
                "failed_queries": num_queries - successful_queries,
            }

    def run_performance_test(
        self,
        num_docs: int = 1000,
        num_queries: int = 100,
    ) -> Dict:
        """Run complete performance test suite.

        Args:
            num_docs: Number of test documents
            num_queries: Number of test queries

        Returns:
            Complete performance metrics
        """
        logger.info("Starting performance test")

        # Generate test data
        documents = generate_test_documents(num_docs)

        # Measure import performance
        import_metrics = self.measure_batch_import(documents)
        logger.info(f"Import metrics: {json.dumps(import_metrics, indent=2)}")

        # Measure search performance
        search_metrics = self.measure_search_performance(num_queries)
        logger.info(f"Search metrics: {json.dumps(search_metrics, indent=2)}")

        # Combine results
        results = {
            "timestamp": datetime.now().isoformat(),
            "weaviate_version": self.client.get_meta().get("version", "unknown"),
            "test_parameters": {
                "num_documents": num_docs,
                "num_queries": num_queries,
                "batch_size": self.batch_size,
            },
            "import_metrics": import_metrics,
            "search_metrics": search_metrics,
        }

        self.results = results
        return results

    def save_results(self, filename: str):
        """Save test results to file.

        Args:
            filename: Output filename
        """
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Saved results to {filename}")


def main():
    """Run performance test suite."""
    # Initialize client
    client = weaviate.Client("http://localhost:8080")

    # Create test instance
    test = WeaviatePerformanceTest(client)

    # Set up schema
    test.setup_schema()

    # Run performance test
    test.run_performance_test()

    # Save results
    test.save_results(f"tests/performance/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")


if __name__ == "__main__":
    main()
