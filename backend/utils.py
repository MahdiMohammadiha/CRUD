from inspectors import BaseInspector


def export_schema_summary(
    inspector: BaseInspector, schema: str = "public"
) -> list:
    """
    Return a list of dictionaries summarizing all tables and their columns
    in the given schema using the provided inspector instance.
    Suitable for JSON response in an API.
    """
    data = []

    # Get all table names from the specified schema
    tables = inspector.get_tables(schema=schema)

    for table in tables:
        # Get all columns for this table
        columns = inspector.get_columns(table)

        # Convert column tuples into structured dicts
        column_list = [
            {"column_name": name, "data_type": dtype} for name, dtype in columns
        ]

        # Append table summary to the list
        data.append({"table": table, "columns": column_list})

    return data
