## About
This project is targeted on building a dynamic data streaming pipeline using GCP. Components of the pipeline include PubSub, Dataflow, BigQuery and others

## Core Functionality
The core ParDo Class function Branch() is responsible for determining the appropriate course of action based on the following cases:

### Case 1: Table Does Not Exist

Add the tag "create_table_branch."
Branch to create a new table.

### Case 2: Table Exists and Schema Matches
Add tag "okay_table_branch"
Insert the record into the existing table.

### Case 3: Table Exists and Schema Has Changed
Add tag "modfiy_table_branch"
Adjust the table's schema as necessary, considering specific conditions.
Table schema adjustments will not accommodate changes in already existing column data types.
Table schema adjustments will ignore the new schema if it is a subset of the existing table schema.
New columns will be appended to the table's schema.

### Case 4: Invalid Data
Add tag "invalid_branch"
Push invalid data to the invalid data PubSub using the standard beam.io method.

### Custom Helper DoFns
CreateTable handles Case 1, which involves creating a new table.
ModifyTable for Case 3
insertToBQ inserts data to big query
Downstream custom DoFns can be used for Case 2, where data should be added to an existing table with a matching schema. Consider using the insert_record DoFn for this purpose.
