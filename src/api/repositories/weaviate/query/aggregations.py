"""Weaviate query aggregations."""

from typing import Any, Dict, List, Optional

from weaviate.classes import Collection
from weaviate.classes.query import Filter


class AggregationBuilder:
    """Builder for Weaviate aggregations."""

    def __init__(self, collection: Collection):
        """Initialize aggregation builder.

        Args:
            collection: Collection reference to build aggregations for
        """
        self.collection = collection
        self.aggregation = collection.aggregate

    def count(self, filter_obj: Optional[Filter] = None) -> int:
        """Get total count with optional filter.

        Args:
            filter_obj: Optional filter to apply

        Returns:
            Total count
        """
        query = self.aggregation.over_all().with_meta_count()
        if filter_obj:
            query = query.with_where(filter_obj)
        result = query.do()
        return result.total_count

    def group_by(self, field: str, filter_obj: Optional[Filter] = None) -> List[Dict[str, Any]]:
        """Group by field with counts.

        Args:
            field: Field to group by
            filter_obj: Optional filter to apply

        Returns:
            List of groups with counts
        """
        query = self.aggregation.over_all().with_group_by([field])
        if filter_obj:
            query = query.with_where(filter_obj)
        result = query.do()
        return result.groups

    def field_stats(self, field: str, filter_obj: Optional[Filter] = None) -> Dict[str, Any]:
        """Get statistics for numeric field.

        Args:
            field: Field to get stats for
            filter_obj: Optional filter to apply

        Returns:
            Statistics including min, max, mean, count
        """
        query = self.aggregation.over_all().with_fields(
            f"""
                minimum {{ {field} }}
                maximum {{ {field} }}
                mean {{ {field} }}
                count {{ {field} }}
                """
        )
        if filter_obj:
            query = query.with_where(filter_obj)
        result = query.do()
        return {
            "min": result.fields.minimum[field],
            "max": result.fields.maximum[field],
            "mean": result.fields.mean[field],
            "count": result.fields.count[field],
        }

    def date_histogram(
        self,
        field: str,
        interval: str = "1d",
        filter_obj: Optional[Filter] = None,
    ) -> List[Dict[str, Any]]:
        """Create date histogram aggregation.

        Args:
            field: Date field to aggregate
            interval: Interval for histogram (e.g., "1d", "1w", "1M")
            filter_obj: Optional filter to apply

        Returns:
            List of buckets with counts
        """
        query = self.aggregation.over_all().with_fields(
            f"""
                histogram {{
                    {field} {{
                        interval: "{interval}"
                    }}
                }}
                """
        )
        if filter_obj:
            query = query.with_where(filter_obj)
        result = query.do()
        return result.fields.histogram[field]

    def terms_aggregation(
        self,
        field: str,
        size: int = 10,
        min_doc_count: int = 1,
        filter_obj: Optional[Filter] = None,
    ) -> List[Dict[str, Any]]:
        """Get most common terms for field.

        Args:
            field: Field to get terms from
            size: Maximum number of terms
            min_doc_count: Minimum document count for term
            filter_obj: Optional filter to apply

        Returns:
            List of terms with counts
        """
        query = self.aggregation.over_all().with_fields(
            f"""
                topTerms {{
                    {field} {{
                        limit: {size}
                        minCount: {min_doc_count}
                    }}
                }}
                """
        )
        if filter_obj:
            query = query.with_where(filter_obj)
        result = query.do()
        return result.fields.top_terms[field]
