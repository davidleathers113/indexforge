"""Weaviate query filters."""

from datetime import datetime
from typing import Any

from weaviate.classes.query import Filter

from src.api.models.requests import DocumentFilter


class FilterBuilder:
    """Builder for Weaviate filters."""

    @staticmethod
    def create_text_filter(field: str, value: str, operator: str = "Equal") -> Filter:
        """Create text filter.

        Args:
            field: Field to filter on
            value: Value to filter by
            operator: Comparison operator

        Returns:
            Filter object
        """
        return Filter.by_property(field).equal(value)

    @staticmethod
    def create_date_filter(field: str, date: datetime, operator: str = "GreaterThan") -> Filter:
        """Create date filter.

        Args:
            field: Field to filter on
            date: Date to filter by
            operator: Comparison operator

        Returns:
            Filter object
        """
        if operator == "GreaterThan":
            return Filter.by_property(field).greater_than(date.isoformat())
        elif operator == "LessThan":
            return Filter.by_property(field).less_than(date.isoformat())
        else:
            return Filter.by_property(field).equal(date.isoformat())

    @staticmethod
    def create_numeric_filter(
        field: str, value: int | float, operator: str = "Equal"
    ) -> Filter:
        """Create numeric filter.

        Args:
            field: Field to filter on
            value: Value to filter by
            operator: Comparison operator

        Returns:
            Filter object
        """
        if operator == "GreaterThan":
            return Filter.by_property(field).greater_than(value)
        elif operator == "LessThan":
            return Filter.by_property(field).less_than(value)
        else:
            return Filter.by_property(field).equal(value)

    @staticmethod
    def create_exists_filter(field: str) -> Filter:
        """Create exists filter.

        Args:
            field: Field to check existence

        Returns:
            Filter object
        """
        return Filter.by_property(field).is_not_none()

    @staticmethod
    def create_in_filter(field: str, values: list[Any]) -> Filter:
        """Create in filter.

        Args:
            field: Field to filter on
            values: List of values to match

        Returns:
            Filter object
        """
        return Filter.by_property(field).contains_any(values)

    @classmethod
    def from_document_filter(cls, filter_params: DocumentFilter) -> Filter | None:
        """Create filter from document filter parameters.

        Args:
            filter_params: Filter parameters

        Returns:
            Combined filter or None if no filters
        """
        filters = []

        if filter_params.file_type:
            filters.append(cls.create_text_filter("file_type", filter_params.file_type))

        if filter_params.date_from:
            filters.append(
                cls.create_date_filter(
                    "metadata_json.modified_at",
                    filter_params.date_from,
                    "GreaterThan",
                )
            )

        if filter_params.date_to:
            filters.append(
                cls.create_date_filter(
                    "metadata_json.modified_at",
                    filter_params.date_to,
                    "LessThan",
                )
            )

        return Filter.and_(filters) if filters else None
