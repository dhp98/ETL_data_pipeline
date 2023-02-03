# ETL_data_pipeline
```
Author: Dhyey Pandya
Email: dhyeyhp2@illinois.edu
```
### Overview

* This data pipeline is made to run in an isolated container in which it polls messages from a standard AWS SQS queue in bathces of 10 messages per iteration.
* In each iteration we extract the message body -> parse json data into a dataframe -> mask IP and Device ID fields with SHA256 hash and store the updated dataframe in postgresql user_logins table in postgresql db.
* After a batch of messages are processed and stored in db, we delete them from the queue and poll for the next batch of messages.
* We stop the process after all the messages in the queue have been processed successfully.
* Below is the basic workflow diagram of the entire pipeline.

<img src="https://user-images.githubusercontent.com/32909781/216669908-9522ee92-8f24-476c-bc9d-938920c7972d.png" width="650" height="400" />


## How to Run
### Pre-requisites
* [install docker](https://docs.docker.com/get-docker/)
* [install postgresql](https://www.postgresql.org/download/)

### Steps to run the pipeline:
* Check if you have docker-compose installed
```
 $ docker-compose --version
```

* Run LocalStack and Postgresql containers
```
 $ docker-compose up --detach
```

* Build and run docker image for data-pipeline
```
 $ docker build -t dhyeypandya/fetch_data_pipeline .
 $ docker run dhyeypandya/fetch_data_pipeline
```

* Open postgresql in new shell and check if the data has been populated in the table
```
 $ psql -d postgres -U postgres -p 5432 -h localhost -W
 psql>$ select * from user_logins; 
```

### Questions

● How would you deploy this application in production?
- Package the application using Docker and deploy over a cluster of machines or Cloud environment in produciton. Monitor it continuously to ensure it runs smoothly, and automate and schedule the pipeline to run at regular intervals using a cron job.

● What other components would you want to add to make this production ready?
- Adding more descriptive error handling and logs to help in debugging.
- Setting up monitoring and alerting components to make sure pipeline runs smoothly all the time with minimal downtime.
- Data backup and recovery to ensure that valuable data is not lost.

● How can this application scale with a growing dataset.
- Parallel processing or Asynchronous handling of each message from queue to scale with increasing data volume.
- Distributed processing using Big Data tools such as Spark, HDFS. 

● How can PII be recovered later on?
- By using reversible hasing techniques or token/key based hashing techniques.

● What are the assumptions you made?
- Devie ID and IP fields are never null.
- Allowing duplicates assuming there is another downstream process responsible for data cleaning.

### Next Steps

* This application can be further organized into a structured data pipeline using Airflow so that dependencies can be managed properly between different serices.
* Changing the current SHA256 hashing to A reversible hashing technique to recover the masked PII.
* Data can also be stored as Documents in NoSQL database like MongoDB, so that we can directly store source json data in its true form.
* Data visualization tools such as PowerBI, Tableau etc can be used on top of stored data for analysis.
* Splunk can also be used to index the data stored in documents/NoSQL db for interactive and rich Data visualization dashboards.


### Resources
* https://hevodata.com/learn/python-sqs/
* https://stackoverflow.com/questions/61749489/getting-could-not-connect-to-the-endpoint-url-error-with-boto3-when-deploying
* https://docs.localstack.cloud/user-guide/integrations/aws-cli/#localstack-aws-cli-awslocal
