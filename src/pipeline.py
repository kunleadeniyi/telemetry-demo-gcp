import apache_beam as beam # strip down to only the modules you need

from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import GoogleCloudOptions
from table_schema import bigquery_table_schemas
from google.cloud import bigquery
import datetime
import os
import json
from dotenv import load_dotenv
load_dotenv()

# from utils import json_deserializer # dataflow fails because it cannot import this dependencies


credential_path = os.getenv("CREDENTIAL_PATH")
project_id = os.getenv("PROJECT_ID")
bigquery_dataset = os.getenv("GBQ_DATASET")
subscription_name = os.getenv("INPUT_SUB")

# auth to google
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

field_type = {
        str: 'STRING',
        bytes: 'BYTES',
        int: 'INTEGER',
        float: 'FLOAT',
        bool: 'BOOLEAN',
        datetime.datetime: 'DATETIME',
        datetime.date: 'DATE',
        datetime.time: 'TIME',
        dict: 'RECORD',
}


# Function to take a dictionary and return a bigquery schema
# https://stackoverflow.com/questions/56079925/autogenerating-bigquery-schema-from-python-dictionary
def map_dict_to_bq_schema(source_dict):
    # SchemaField list
    schema = []
    # Iterate the existing dictionary
    for key, value in source_dict.items():
        try:
            schemaField = bigquery.SchemaField(key, field_type[type(value)]) # NULLABLE BY DEFAULT
        except KeyError:
            # We are expecting a REPEATED field
            if value and len(value) > 0:
                schemaField = bigquery.SchemaField(key, field_type[type(value[0])], mode='REPEATED') # REPEATED

        # Add the field to the list of fields
        schema.append(schemaField)

        # If it is a STRUCT / RECORD field we start the recursion
        if schemaField.field_type == 'RECORD':
            schemaField._fields = map_dict_to_bq_schema(value)

    # Return the dictionary values
    return schema


def dynamic_insert_to_bq(event):
    # try:
    #     event = json.loads(event)
    # except ValueError as ve:
    #     print(f"Failed to parse data: {ve}")

    # check for necessary fields
    if "table_name" not in event or "data" not in event:
        print("event is missing required fields")
        return
    
    # get table_name and data from event
    table_name = event["table_name"]
    data = event["data"]

    bq_client = bigquery.Client()

    dataset_id = bigquery_dataset
    table_id = f"{dataset_id}.{table_name}"
    table_ref = bq_client.dataset(dataset_id).table(table_name)

    try:
        # table_ref = bq_client.dataset(dataset_id).table(table_name)
        bq_client.get_table(table_ref)
    except Exception as e:
        # print(bigquery_table_schemas[table_name])
        schema = map_dict_to_bq_schema(data)

        table = bigquery.Table(table_ref=table_ref, schema=schema)
        table = bq_client.create_table(table=table)

    try:
        bq_client.insert_rows_json(table_id, [data])
    except Exception as e:
        print(f"Error while inserting into table {e}")


pipeline_options = PipelineOptions(
    project=project_id,
    job_name="python-pubsub-to-bq-dynamic-table", 
    save_main_session=True, 
    streaming=True
    , runner='DataFlowRunner',
    staging_location="gs://demo-storage-bucket-401116/dataflow_temp",
    temp_location="gs://demo-storage-bucket-401116/dataflow_temp", region="europe-west2",
    requirements_file = "requirements.txt",
    setup_file = "src/setup.py"
)


def run():
    pipeline = beam.Pipeline(options=pipeline_options)

    # subscription format -> projects/<project>/subscriptions/<subscription>
    read_from_pubsub = (
            pipeline | "Read from Pub/Sub"
            >> beam.io.ReadFromPubSub(subscription=f"projects/{project_id}/subscriptions/{subscription_name}"))

    # parse_messages = read_from_pubsub | "Parse to JSON"
    # >> beam.Map(json_deserializer) # commented out because of json_deserializer import issues, replaced with line below
    parse_messages = read_from_pubsub | "Parse to JSON" >> beam.Map(lambda x: json.loads(x.decode('utf-8')))

    write_to_bq = parse_messages | "Write to BigQuery Table" >> beam.ParDo(dynamic_insert_to_bq)
    parse_messages | beam.Map(print)

    pipeline.run().wait_until_finish()


if __name__ == "__main__":
    run()

    # event = {'table_name': 'users', 
    #  'data': {'session_id': 13345021569, 
    #           'first_name': 'Thomas', 
    #           'last_name': 'Brock', 
    #           'address': '02785 Brooke Club\nSmithville, KS 26651', 
    #           'location_lat': 13, 
    #           'location_lon': 41
    #           }
    # }
    # dynamic_insert_to_bq(event=event)
