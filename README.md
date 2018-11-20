# RDSS OAI-PMH Adaptor


[![Build Status](https://travis-ci.com/JiscRDSS/rdss-oai-pmh-adaptor.svg?branch=develop)](https://travis-ci.com/JiscRDSS/rdss-oai-pmh-adaptor)

## Introduction

The RDSS OAI-PMH Adaptor is a per-institutional adaptor for use by institutions that utilise instances of the [EPrints open access repository](http://www.eprints.org/), or the [DSpace digital repository](https://duraspace.org/dspace/).

The adaptor will execute periodically, querying the OAI-PMH endpoint exposed by the OAI-PMH provider to retrieve records that have been added to the repository since the creation timestamp of the most recently retrieved record. Once the record is retrieved, its corresponding digital objects are retrieved and stored in an S3 bucket, and its metadata is converted into a format compliant with the Jisc RDSS canonical data model. It is then published into the messaging system, for consumption by downstream systems.

When the RDSS OAI-PMH adaptor is configured to target DSpace, it will query for records in both the `oai_dc` format and the `ore` format, using the latter to get the locations of files related to the record. When it is configured to target EPrints, it will only query for records in the `oai_dc` format, and use the `identifier` field to give the location of files related to the record.

The RDSS OAI-PMH Adaptor is capable of interacting with any OAI-PMH compliant endpoint.

## Language / Framework

* Python 3.6+
* Docker

## Service Architecture

The adaptor runs as a Docker container which can be configured to point to a OAI-PMH endpoint. It also requires DynamoDB tables and S3 buckets to operate - all of this infrastructure is created through the [accompanying Terraform](https://github.com/JiscRDSS/rdss-institutional-ecs-clusters/tree/develop/infra-oai-pmh-adaptor/tf).

The following environmental variables are required for the adaptor to run. These are typically provided as parameters to the Docker container:

* `JISC_ID`
  * The Jisc ID of the institution that is operating the OAI-PMH provider.

* `ORGANISATION_NAME`
  * The name of the institution that is operating the OAI-PMH provider.

* `OAI_PMH_PROVIDER`
  * The name of the application providing the OAI-PMH endpoint. Must be one of `eprints` or `dspace`.

* `OAI_PMH_ENDPOINT_URL`
  * The URL of the OAI-PMH endpoint.

* `DYNAMODB_WATERMARK_TABLE_NAME`
  * The name of the DynamoDB table where the high watermark of the adaptor is persisted.

* `DYNAMODB_PROCESSED_TABLE_NAME`
  * The name of the DynamoDB table where the status of processed records are recorded.

* `S3_BUCKET_NAME`
  * The name of the S3 bucket used to persist the digital objects retrieved from the OAI-PMH provider.

* `OUTPUT_KINESIS_STREAM_NAME`
  * The name of the Kinesis stream where the messages generated by the adaptor are pushed to for consumption by downstream systems.

* `OUTPUT_KINESIS_INVALID_STREAM_NAME`
  * The name of the Kinesis stream where invalid generated messages are pushed to.

* `RDSS_MESSAGE_API_SPECIFICATION_VERSION`
  * The version of the Jisc RDSS API specification that generated messages are validated against. (n.b. this does not affect the structure of the generated messages)

## Developer Setup

To run the adaptor locally, configure all the required environmental variables described above. To create the local virtual environment, install dependencies and manually run the adaptor:

```
make env
source ./env/bin/activate
make deps
python run.py
```

### Testing

To run the test suite for the RDSS OAI-PMH Adaptor, run the following command:

```
pytest
```

## Frequently Asked Questions

## Will the adaptor work with any OAI-PMH endpoint?
In theory the adaptor should work with any OAI-PMH endpoint, as the base mapping of metadata to the [RDSS Canonical Data Model](https://github.com/JiscRDSS/rdss-canonical-data-model/) uses the Dublin Core (DC) metadata response which all OAI-PMH implementations must support. In practice there is significant variation in the content of this metadata, and it is likely that some customisation of this is necessary for different OAI-PMH providers and institutions.

At present when the RDSS OAI-PMH Adaptor is targeted at an Eprints instance, the location of files related to the record must be extracted from this DC metadata as Eprints does not provide OAI-ORE (or other) output. This working correctly is dependent on the `identifier` field containing a link to the associated file, the presence of which is not guaranteed.  

## How do I reset the adaptor to re-process records from the targeted OAI-PMH endpoint?
The following two steps are required to force the adaptor to re-process records.
1) Records that are to be re-processed should be removed from the table defined by the `DYNAMODB_PROCESSED_TABLE_NAME`, the key for rows in this table being the identifier of the record within the OAI-PMH provider.
2) The `Value` of the `HighWatermark` stored in table defined by the `DYNAMODB_WATERMARK_TABLE_NAME` environmental variable must be set to an ISO 8601 datetime string prior to the datestamp of the earliest record that is to be re-processed.
