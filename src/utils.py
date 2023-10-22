import json
from faker import Faker

def json_serializer(v):
    return json.dumps(v).encode('utf-8')

def json_deserializer(v):
    return json.loads(v.decode('utf-8'))

def wrap_data(table_name, data):
    return {
        "table_name": table_name,
        "data": data
    }