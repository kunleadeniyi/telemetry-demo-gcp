import apache_beam as beam  # strip down to only the modules you need

from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.runners.pipeline_context import pvalue
from apache_beam.options.pipeline_options import GoogleCloudOptions
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict

# Imports the Cloud Logging client library
import google.cloud.logging

import datetime
import os
import json
import logging
from dotenv import load_dotenv
load_dotenv()

# from utils import json_deserializer # dataflow fails because it cannot import this dependencies

credential_path = os.getenv("CREDENTIAL_PATH")
project_id = os.getenv("PROJECT_ID")
bigquery_dataset = os.getenv("GBQ_DATASET")
valid_pubsub = os.getenv("VALID_PUBSUB_TOPIC")
invalid_pubsub = os.getenv("INVALID_PUBSUB_TOPIC")
subscription_name = os.getenv("INPUT_SUB")
gcp_bucket = os.getenv("GCP_BUCKET")
# auth to google
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

# Instantiates a client
# gcp_logging_client = google.cloud.logging.Client()
# gcp_logging_client.setup_logging()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

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
        # list: 'ARRAY'
}

# global BQ client
# bq_client = bigquery.Client() # Had to declare locally to avoid _pickle.PicklingError
# https://cloud.google.com/dataflow/docs/guides/common-errors (NameError Section)

# pipeline options
pipeline_options = PipelineOptions(
    project=project_id,
    job_name="python-pubsub-to-bq-dynamic-table",
    save_main_session=True,
    streaming=True
    # , runner='DataFlowRunner',
    # staging_location=f"gs://{gcp_bucket}/dataflow_staging",
    # temp_location=f"gs://{gcp_bucket}/dataflow_temp", region="europe-west2",
    # requirements_file="../requirements.txt",
    # # setup_file="src/setup.py"
)


# Function to take a dictionary and return a bigquery schema
# https://stackoverflow.com/questions/56079925/autogenerating-bigquery-schema-from-python-dictionary
def map_dict_to_bq_schema(source_dict):
    """
    Args:
        source_dict: Equivalent to the element/message to be ingested. Format: dictionary

    Returns:
        An array suitable to pass for a Bigquery Schema
    """
    # SchemaField list
    schema = []

    # Iterate through source_dict
    for key, value in source_dict.items():
        try:
            # timestamps have to converted to strings to be json serialized
            # if condition attaches appropriate timestamp format if timestamp is in the column name instead of string
            if "timestamp" in key:
                schema_field = bigquery.SchemaField(key, 'TIMESTAMP')
            else:
                schema_field = bigquery.SchemaField(key, field_type[type(value)])  # NULLABLE BY DEFAULT
        except KeyError:
            # We are expecting a REPEATED field
            if value and len(value) > 0:
                schema_field = bigquery.SchemaField(key, field_type[type(value[0])], mode='REPEATED')  # REPEATED

        # Add the field to the list of fields
        if schema_field not in schema:  # if condition to fix weird bug where a key (field name) appears twice!! make no sense
            schema.append(schema_field)

        # If it is a STRUCT / RECORD field we start the recursion
        if schema_field.field_type == 'RECORD':
            schema_field._fields = map_dict_to_bq_schema(value)

    # Return the dictionary values
    return schema


def check_table_exists(table_name):
    try:
        bq_client = bigquery.Client()
        dataset_id = bigquery_dataset
        table_id = f"{dataset_id}.{table_name}"
        table = bq_client.get_table(table_id)
        # print(f"table ref - {table.dataset_id}.{table.table_id}")
        return table
    except NotFound:
        return None


# def schema_is_subset(existing_schema, new_schema):
schema_cache = {}


class Branch(beam.DoFn):

    def __init__(self):
        self.schema_cache = {}

    def map_inner_record_to_bq_schema(self, nested_record):
        schema = []
        # Iterate the existing dictionary
        for key, value in nested_record.items():
            try:
                if "timestamp" in key:
                    schema_field = bigquery.SchemaField(key, 'TIMESTAMP')
                else:
                    schema_field = bigquery.SchemaField(key, field_type[type(value)])  # NULLABLE BY DEFAULT
            except KeyError:
                # We are expecting a REPEATED field
                if value and len(value) > 0:
                    schema_field = bigquery.SchemaField(key, field_type[type(value[0])], mode='REPEATED')  # REPEATED

            # Add the field to the list of fields
            schema.append(schema_field)

        # Return the dictionary values
        return tuple(schema)

    def map_dict_to_bq_schema(self, element):
        # SchemaField list
        schema = []
        # Iterate the existing dictionary
        for key, value in element['data'].items():
            try:
                if "timestamp" in key:
                    schema_field = bigquery.SchemaField(key, 'TIMESTAMP')
                else:
                    schema_field = bigquery.SchemaField(key, field_type[type(value)]) # NULLABLE BY DEFAULT
            except KeyError:
                # We are expecting a REPEATED field
                if value and len(value) > 0:
                    schema_field = bigquery.SchemaField(key, field_type[type(value[0])], mode='REPEATED')  # REPEATED

            # Add the field to the list of fields
            schema.append(schema_field)

            # If it is a STRUCT / RECORD field we start the recursion
            if schema_field.field_type == 'RECORD':
                schema_field._fields = self.map_inner_record_to_bq_schema(value)

        # Return the dictionary values
        table_name = element['table_name']
        # schema_cache[table_name] = schema
        self.schema_cache[table_name] = schema
        return schema

    def process(self, element):
        # edge case
        if (element.get("table_name") is None) or (element.get("data") is None):
            yield pvalue.TaggedOutput(tag='invalid_branch', value=element)
            # print("Invalid Branch")

        else:
            table_name = element['table_name']
            data = element['data']
            # print(table_name)
            table_object = check_table_exists(table_name)
            if table_object is not None:  # the table exists branch to either insert record or update schema then insert
                # self.schema_cache[table_name] = table_object.schema
                # yield pvalue.TaggedOutput(tag='table_exist', value=element)
                # schema_check = self.check_schema(table_object.schema, map_dict_to_bq_schema(data))  # return bool
                schema_check = table_object.schema == schema_cache.get(table_name)
                # schema_check = table_object.schema == self.schema_cache.get(table_name)

                if schema_check:
                    element['data']['full_table_id'] = table_object.full_table_id

                    # element['table'] = table_object
                    # yield pvalue.TaggedOutput(tag='okay_table_branch', value=element)

                    # element = element['data']
                    # table = element['table_name']

                    # element = (f"{project_id}.{bigquery_dataset}.{table_name}", data)
                    element = element['data']
                    yield pvalue.TaggedOutput(tag='okay_table_branch', value=element)
                    logging.info(f"schema validation passed, data okay to insert \npcoll: {element}")
                elif not schema_check:
                    # print("Modifying and attaching schema to element with key 'new_schema' ")
                    # new_schema = map_dict_to_bq_schema(data)

                    element['data']['full_table_id'] = table_object.full_table_id
                    new_schema = self.map_dict_to_bq_schema(element)

                    schema_cache[table_name] = new_schema
                    element['new_schema'] = new_schema
                    element['table'] = table_object

                    yield pvalue.TaggedOutput(tag='modify_table_branch', value=element)
            else:  # create table
                # print("Create table")
                element['data']['full_table_id'] = f"{project_id}.{bigquery_dataset}.{element['table_name']}"

                self.schema_cache[table_name] = map_dict_to_bq_schema(data)
                yield pvalue.TaggedOutput(tag='create_table_branch', value=element)


class CreateTable(beam.DoFn):
    def process(self, element):
        table_id = f"{project_id}.{bigquery_dataset}.{element['table_name']}"
        schema = map_dict_to_bq_schema(element['data'])
        table = bigquery.Table(table_id, schema=schema)

        bq_client = bigquery.Client()

        try:
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                # assumes all events are sent with event_timestamp field
                field="event_timestamp",  # name of column to use for partitioning
            )
            table.require_partition_filter = True
            table = bq_client.create_table(table)
            logging.info("Created table {}.{}.{}".format(table.project, table.dataset_id,
                                                  table.table_id))  # change to logging event
        except Conflict:  # to handle response 409 from big query
            pass
        except Exception as e:
            logging.exception(f"Exception in Create Table: {e}")

        element['table'] = table

        logging.debug(f"CreateTable DoFn called for table id: {table_id} - calling InsertToBQ function next")
        yield element


class InsertToBQ(beam.DoFn):
    def process(self, element):
        # full_table_id = element['full_table_id']
        # table_id = f"{element['table'].project_id}.{element['table'].dataset_id}.{element['table'].table_id}"
        table_id = element['table'].full_table_id.replace(':', '.')
        data = element['data']

        bq_client = bigquery.Client()
        try:
            # bq_client.insert_rows_json(full_table_id, [data])
            logging.debug(f"InsertToBQ function call - table id: {table_id}")
            bq_client.insert_rows_json(table_id, [data])
            logging.debug(f"data inserted: {data}")
        except Exception as e:
            logging.warning(f"Encountered exception when inserting {data} to bigquery: {e}")  # change to logging event

    # edge case


class ModifyTable(beam.DoFn):
    def generate_updated_schema(self, existing_schema, new_schema):
        # Convert SchemaField objects to a hashable form (e.g., tuples)
        existing_schema_set = set((field.name, field.field_type, field.mode) if field.field_type != 'RECORD' else (
        field.name, field.field_type, field.mode, tuple(field.fields)) for field in existing_schema)
        new_schema_set = set((field.name, field.field_type, field.mode) if field.field_type != 'RECORD' else (
        field.name, field.field_type, field.mode, tuple(field.fields)) for field in new_schema)

        # Create updated schema by combining existing schema and new schema
        updated_schema_set = existing_schema_set.union(new_schema_set)

        # Convert the hashable form back to SchemaField objects
        updated_schema_objects = []
        for field_info in updated_schema_set:
            if field_info[1] == 'RECORD':
                updated_schema_objects.append(
                    bigquery.SchemaField(field_info[0], 'RECORD', field_info[2], fields=field_info[3]))
            else:
                updated_schema_objects.append(bigquery.SchemaField(*field_info[:3]))

        logging.info(f"Modify Table DoFn updated schema generation: {updated_schema_objects} ")
        return updated_schema_objects

    def process(self, element):
        table = element['table']
        existing_schema = table.schema
        # new_schema = element['new_schema']
        new_schema = element.get('new_schema')
        # modified_schema = generate_updated_schema(existing_schema, new_schema)
        modified_schema = self.generate_updated_schema(existing_schema, new_schema)
        # table.schema = modified_schema # moving this to the bottom after get_table

        # schema_cache[table.table_id] = table.schema
        print(existing_schema)
        print(new_schema)
        bq_client = bigquery.Client()

        try:
            # https://stackoverflow.com/questions/68362833/bigquery-patch-precondition-check-failed
            table = bq_client.get_table(table.full_table_id.replace(':', '.'))  # to fix patch 412 precondition exception
            table.schema = modified_schema
            table = bq_client.update_table(table, ['schema'])
            # print(f"ModifyTable DoFn Schema check: {existing_schema == new_schema}")
            # print(existing_schema)
            # print(new_schema)
            logging.info(f"schema modified: new_schema - {table.schema}")
            # print(f"Table schema updated to: \n{table.schema}") # change to logging event
            yield element
        except Exception as e:
            logging.error(f"Error modifying schema: {e}")


def run():

    gcp_logging_client = google.cloud.logging.Client()
    gcp_logging_client.setup_logging()
    # with beam.Pipeline(options=pipeline_options) as pipeline:
    pipeline = beam.Pipeline(options=pipeline_options)

    parsed_data = (
        pipeline
        | "Read_from_PubSub" >> beam.io.ReadFromPubSub(subscription=f"projects/{project_id}/subscriptions/{subscription_name}")
        | "Parse_to_JSON" >> beam.Map(lambda x: json.loads(x.decode('utf-8')))
        # | "flatten" >> beam.Flatten()
        # | "print" >> beam.Map(print)
    )

    branches = (
        parsed_data
        # | 'Tagged branches' >> beam.ParDo(Branch()).with_outputs()  # .with_outputs("a", "b")
        | 'Tagged_branches' >> beam.ParDo(Branch()).with_outputs()
        # | beam.Map(print)
    )

    invalid = (
            branches.invalid_branch
            # | 'print invalid data' >>  beam.Map(print)
            | 'serialise_to_bytes' >> beam.Map(lambda x: json.dumps(x).encode('utf-8'))
            | 'push_to_invalid_topic' >> beam.io.WriteToPubSub(topic=f"projects/{project_id}/topics/{invalid_pubsub}", )
    )

    create = (
            branches.create_table_branch
            | 'create_table' >> beam.ParDo(CreateTable())
            # | 'print create table' >> beam.Map(print)
            # | 'insert to new table' >> beam.ParDo(InsertToBQ())
            | 'extract_data' >> beam.Map(lambda element: element['data'])
            | "write_after_create" >> beam.io.WriteToBigQuery(
                table=lambda element: element['full_table_id'],
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                method='STREAMING_INSERTS'
            )
    )

    modify = (
            branches.modify_table_branch
            | 'modify_table' >> beam.ParDo(ModifyTable())
            | 'insert_to_modified_table' >> beam.ParDo(InsertToBQ())
            # | 'print modify table' >> beam.Map(print)

    )

    insert = (
            # extract_data
            branches.okay_table_branch
              # | beam.Map(print)
            | "write_to_bigQuery" >> beam.io.WriteToBigQuery(
                table=lambda element: element['full_table_id'],
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                method='STREAMING_INSERTS',
                insert_retry_strategy='RETRY_NEVER'
            )
    )

    errors = (
            # result | beam.Map(print)
        insert['FailedRows']
        | "Failed Inserts" >> beam.Map(print)
        # | 'serialise_failed_writes' >> beam.Map(lambda x: json.dumps(x).encode('utf-8'))
        # | 'push_failed_writes_to_invalid_topic' >> beam.io.WriteToPubSub(topic=f"projects/{project_id}/topics/{invalid_pubsub}", )
    )

    pipeline.run().wait_until_finish()


if __name__ == "__main__":
    run()
