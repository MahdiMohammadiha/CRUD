from inspectors import BaseInspector


def export_schema_summary(inspector: BaseInspector, schema: str = "public") -> list[dict]:
    """
    Return a list of dictionaries summarizing all tables and their columns
    in the given schema using the provided inspector instance.
    Suitable for JSON response in an API.
    """
    data = []

    tables = inspector.get_tables(schema=schema)
    for table in tables:
        columns = inspector.get_columns(table)
        column_list = [
            {"column_name": name, "data_type": dtype}
            for name, dtype in columns
        ]
        data.append({
            "table": table,
            "columns": column_list
        })

    return data
