import apache_beam as beam  # strip down to only the modules you need

from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.runners.pipeline_context import pvalue
from apache_beam.options.pipeline_options import GoogleCloudOptions
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict

import datetime
import os
import json
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
bq_client = bigquery.Client()

# pipeline options
pipeline_options = PipelineOptions(
    project=project_id,
    job_name="python-pubsub-to-bq-dynamic-table",
    # save_main_session=True,
    streaming=True
    # , runner='DataFlowRunner',
    # staging_location=f"gs://{gcp_bucket}/dataflow_staging",
    # temp_location=f"gs://{gcp_bucket}/dataflow_temp", region="europe-west2",
    # requirements_file="requirements.txt",
    # setup_file="src/setup.py"
)


# Function to take a dictionary and return a bigquery schema
# https://stackoverflow.com/questions/56079925/autogenerating-bigquery-schema-from-python-dictionary
def map_dict_to_bq_schema(source_dict):
    # SchemaField list
    schema = []
    # Iterate the existing dictionary
    for key, value in source_dict.items():
        try:
            schema_field = bigquery.SchemaField(key, field_type[type(value)])  # NULLABLE BY DEFAULT
        except KeyError:
            # We are expecting a REPEATED field
            if value and len(value) > 0:
                schema_field = bigquery.SchemaField(key, field_type[type(value[0])], mode='REPEATED')  # REPEATED

        # Add the field to the list of fields
        schema.append(schema_field)

        # If it is a STRUCT / RECORD field we start the recursion
        if schema_field.field_type == 'RECORD':
            schema_field._fields = map_dict_to_bq_schema(value)

    # Return the dictionary values
    return schema


def check_schema(bigquery_schema: list, elem_schema: list):
    output = False
    # output = True
    if bigquery_schema == elem_schema:
        output = True
        return output

    print(f"ELEM SCHEMA: {elem_schema} \n type: {type(elem_schema)}")
    if set(elem_schema).issubset(bigquery_schema):
        output = True
        return output

    return output


def check_table_exists(table_name):
    try:
        # bq_client = bigquery.Client()
        dataset_id = bigquery_dataset
        table_id = f"{dataset_id}.{table_name}"
        table = bq_client.get_table(table_id)
        # print(f"table ref - {table.dataset_id}.{table.table_id}")
        return table
    except NotFound:
        return None


def generate_updated_schema(existing_schema, new_schema):
    updated_schema = existing_schema + list(set(new_schema) - set(existing_schema))
    return updated_schema


# def schema_is_subset(existing_schema, new_schema):

class Branch(beam.DoFn):
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
                # yield pvalue.TaggedOutput(tag='table_exist', value=element)
                schema_check = check_schema(table_object.schema, map_dict_to_bq_schema(data))  # return bool
                if schema_check:
                    # element['full_table_id'] = table_object.full_table_id
                    element['table'] = table_object
                    yield pvalue.TaggedOutput(tag='okay_table_branch', value=element)
                elif not schema_check:
                    # print("Modifying and attaching schema to element with key 'new_schema' ")
                    new_schema = map_dict_to_bq_schema(data)
                    element['new_schema'] = new_schema
                    element['table'] = table_object
                    yield pvalue.TaggedOutput(tag='modify_table_branch', value=element)
            else:  # create table
                # print("Create table")
                yield pvalue.TaggedOutput(tag='create_table_branch', value=element)

                # yield (table_name, data)
                # yield pvalue.TaggedOutput(plant['name'], plant)


class CreateTable(beam.DoFn):
    def process(self, element):
        table_id = f"{project_id}.{bigquery_dataset}.{element['table_name']}"
        schema = map_dict_to_bq_schema(element['data'])
        table = bigquery.Table(table_id, schema=schema)

        try:
            table = bq_client.create_table(table)
            print("Created table {}.{}.{}".format(table.project, table.dataset_id,
                                                  table.table_id))  # change to logging event
        except Conflict:  # to handle response 409 from big query
            pass

        element['table'] = table
        yield element


class InsertToBQ(beam.DoFn):
    def process(self, element):
        # full_table_id = element['full_table_id']
        table_id = f"{element['table'].dataset_id}.{element['table'].table_id}"
        data = element['data']
        try:
            # bq_client.insert_rows_json(full_table_id, [data])
            bq_client.insert_rows_json(table_id, [data])
            print(data)
        except Exception as e:
            print(f"Encountered exception when inserting {data} to bigquery: {e}")  # change to logging event

    # edge case


class ModifyTable(beam.DoFn):
    def process(self, element):
        table = element['table']
        existing_schema = table.schema
        new_schema = element['new_schema']
        modified_schema = generate_updated_schema(existing_schema, new_schema)

        table.schema = modified_schema
        table = bq_client.update_table(table, ['schema'])
        print(existing_schema == new_schema)
        print(existing_schema)
        print(new_schema)

        yield element
        # print(f"Table schema updated to: \n{table.schema}") # change to logging event

# def check_schema(table_name, source_dict):
#     # get existing schema
#     bq_client = bigquery.Client()
#     dataset_id = bigquery_dataset
#     table_id = f"{dataset_id}.{table_name}"
#     # table = bq_client.get_table(table_id)
#
#     try:
#         table = bq_client.get_table(table_id)  # Make an API request.
#
#         # check schema
#         existing_schema = table.schema
#
#         # generate new schema
#         new_schema = map_dict_to_bq_schema(source_dict['data'])
#         # print(f"New Schema: {new_schema}")
#
#         if existing_schema == new_schema:
#             return True
#         # update below conditional to
#         # - skip update if schema is a subset of new schema
#         # - raise an exception if an existing column type is changed (we don't want to change column types)
#
#         else:
#             return False
#             # modified_schema = generate_updated_schema(existing_schema, new_schema)
#             # table.schema = modified_schema
#             # table = bq_client.update_table(table, ['schema'])
#             # print(f"Table schema updated to: \n{table.schema}")
#
#     except NotFound as nf:
#         print(f"Table {table_id} is not found.")
#         print(f"Exception Raised: {nf}")


# def dynamic_insert_to_bq(event):
#     # check for necessary fields
#     if "table_name" not in event or "data" not in event:
#         print("event is missing required fields")
#         return
#
#     # get table_name and data from event
#     table_name = event["table_name"]
#     data = event["data"]
#
#     bq_client = bigquery.Client()
#
#     dataset_id = bigquery_dataset
#     table_id = f"{dataset_id}.{table_name}"
#     table_ref = bq_client.dataset(dataset_id).table(table_name)
#
#     try:
#         # table_ref = bq_client.dataset(dataset_id).table(table_name)
#         # bq_client.get_table(table_ref)
#         table = bq_client.get_table(table_id)
#     except Exception as e:
#         # print(bigquery_table_schemas[table_name])
#         schema = map_dict_to_bq_schema(data)
#
#         table = bigquery.Table(table_ref=table_ref, schema=schema)
#         table = bq_client.create_table(table=table)
#
#     try:
#         bq_client.insert_rows_json(table_id, [data])
#     except Exception as e:
#         print(f"Error while inserting into table {e}") # change to logging event


# def run():
#     pipeline = beam.Pipeline(options=pipeline_options)
#
#     # subscription format -> projects/<project>/subscriptions/<subscription>
#     read_from_pubsub = (
#             pipeline | "Read from Pub/Sub"
#             >> beam.io.ReadFromPubSub(subscription=f"projects/{project_id}/subscriptions/{subscription_name}"))
#
#     # parse_messages = read_from_pubsub | "Parse to JSON"
#     # >> beam.Map(json_deserializer) # commented out because of json_deserializer import issues, replaced with line below
#     parse_messages = read_from_pubsub | "Parse to JSON" >> beam.Map(lambda x: json.loads(x.decode('utf-8')))
#
#     write_to_bq = parse_messages | "Write to BigQuery Table" >> beam.ParDo(dynamic_insert_to_bq)
#     parse_messages | beam.Map(print)
#
#     pipeline.run().wait_until_finish()

def run():
    pipeline = beam.Pipeline(options=pipeline_options)
    # branches = (
    #         pipeline
    #         | 'Input data' >> beam.Create([
    #     {'data': {'name': 'Strawberry', 'season': 2}},  # April, 2020
    #     {'table_name': 'veggies', 'data': {'name': 'Carrot', 'season': 3}},  # June, 2020
    #     {'table_name': 'test_assets', 'data': {'name': 'Artichoke', 'season': 4}},  # March, 2020
    #     {'table_name': 'veggies', 'data': {'name': 'Tomato', 'season': 5}},  # May, 2020
    #     {'table_name': 'veggies', 'data': {'name': 'Potato', 'season': 6}},  # September, 2020
    #     # event
    # ])
    # )

    branches = (
        pipeline
        | "Read from Pub/Sub" >> beam.io.ReadFromPubSub(subscription=f"projects/{project_id}/subscriptions/{subscription_name}")
        | "Parse to JSON" >> beam.Map(lambda x: json.loads(x.decode('utf-8')))
        | 'Tagged branches' >> beam.ParDo(Branch()).with_outputs()  # .with_outputs("a", "b")
        # | beam.Map(print)
    )

    # print(branches)
    invalid = (
            branches.invalid_branch
            # | 'print invalid data' >>  beam.Map(print)
            | 'serialise to bytes' >> beam.Map(lambda x: json.dumps(x).encode('utf-8'))
            | 'push to invalid Topic' >> beam.io.WriteToPubSub(topic=f"projects/{project_id}/topics/{invalid_pubsub}", )
    )

    create = (
            branches.create_table_branch
            | 'create table' >> beam.ParDo(CreateTable())
            # | 'print create table' >> beam.Map(print)
            | 'insert to new table' >> beam.ParDo(InsertToBQ())
    )

    modify = (
            branches.modify_table_branch
            | 'modify table' >> beam.ParDo(ModifyTable())
            | 'insert to modified table' >> beam.ParDo(InsertToBQ())
            # | 'print modify table' >> beam.Map(print)

    )

    insert = (
            branches.okay_table_branch | 'insert to table' >> beam.ParDo(InsertToBQ())
    )

    pipeline.run().wait_until_finish()


if __name__ == "__main__":
    run()

    event = {
        'table_name': 'test_player',
        'data': {
             'player_id': 'qwertyuiop',
             'username': 'jd', 'first_name': 'John',  'last_name': 'Doe',
             'email': 'campbelljuan@example.com', 'level': 1, 'points': 500, 'coins': 10,
             'xp': 1, 'created_at': 1699103979.483098, 'last_login_date': '04-11-2023',
             'platform': 'PC', 'region': 'Europe', 'source': 'Steam'
             }
        }

    # with beam.Pipeline() as pipeline:

    # event = {'table_name': 'users',
    #  'data': {'session_id': 13345021569,
    #           'first_name': 'Thomas',
    #           'last_name': 'Brock',
    #           'address': '02785 Brooke Club\nSmithville, KS 26651',
    #           'location_lat': 13,
    #           'location_lon': 41
    #           }
    # }

    #
    # print(check_schema(table_name="test_players", source_dict=event))
    # dynamic_insert_to_bq(event=event)


# to add
# 1. add ingest/process_timestamp to each entry in the pipeline
# 2. modify schema on the go as another branch of the pipeline
# 3. test arrays
# 4. test json
# 5. partition by day
