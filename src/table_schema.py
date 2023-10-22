from apache_beam.io.gcp.internal.clients import bigquery
from apache_beam.io.gcp.bigquery_tools import parse_table_schema_from_json
import json

bigquery_table_schemas = {
    "users": {
        "fields": [
            {"name": "session_id", "type": "INTEGER"},
            {"name": "first_name", "type": "STRING"},
            {"name": "last_name", "type": "STRING"},
            {"name": "address", "type": "STRING"},
            {"name": "location_lat", "type": "INTEGER"},
            {"name": "location_lon", "type": "INTEGER"},
        ]
    },

    "user": {
    "fields": [
        {"name": "session_id", "type": "INTEGER"},
        {"name": "first_name", "type": "STRING"},
        {"name": "last_name", "type": "STRING"},
        {"name": "address", "type": "STRING"},
        {"name": "location_lat", "type": "INTEGER"},
        {"name": "location_lon", "type": "INTEGER"},
    ]
    }
}

def _parse_schema_field(field):
    """Parse a single schema field from dictionary.

    Args:
        field: Dictionary object containing serialized schema.

    Returns:
        A TableFieldSchema for a single column in BigQuery.
    """
    schema = bigquery.TableFieldSchema()
    schema.name = field['name']
    schema.type = field['type']
    if 'mode' in field:
        schema.mode = field['mode']
    else:
        schema.mode = 'NULLABLE'
    if 'description' in field:
        schema.description = field['description']
    if 'fields' in field:
        schema.fields = [_parse_schema_field(x) for x in field['fields']]
    return schema


if __name__ == "__main__":
    table_name = "users"
    print(bigquery_table_schemas[table_name]["fields"])

    # print( [_parse_schema_field(f) for f in bigquery_schema[table_name]['fields']] )

    print(parse_table_schema_from_json(json.dumps(bigquery_table_schemas[table_name])))