# Git LFS

[Git Large File Storage](https://git-lfs.github.com) (Git LFS) is an extension to Git that allows you to work with large files the same way as other text files but store it on separate remote servers.
This project contains a set of modules for deploying custom Git LFS servers on different infrastructure providers.
Implemented [Batch API](https://github.com/git-lfs/git-lfs/blob/master/docs/api/batch.md) to request the ability to transfer LFS objects with the LFS server.

Inspired by [Serverless Git LFS for Game Development - Alan Edwardes](https://alanedwardes.com/blog/posts/serverless-git-lfs-for-game-dev/).

### AWS

Module AWS allows you to use [Amazon S3](https://aws.amazon.com/s3/) as remote storage for large files.
Service is deployable on a serverless stack (API Gateway + Lambda) that allows you to use Pay-As-You-Go (PAYG) pricing model.
The high-level solution diagram you can find below.

![architecture](https://app.lucidchart.com/publicSegments/view/b1679e24-9a07-40b6-aeef-53fcb77ee56e/image.png)

When user push/pull (1) changes Git LFS client make Batch API request (2) over HTTPS to Amazon API Gateway service which in turn proxies (3) request to AWS Lambda.
In lambda function for each LFS object generated presigned URL for temporary write/read access to S3.
After processing the result returned (4) to API Gateway that turn back (5) response to Git LFS client.
Now Git LFS client ready for uploading (6) / downloading (7) objects to/from S3 using presigned URL.

### Azure

Module Azure allows you to use [Azure Blob Storage](https://azure.microsoft.com/en-us/services/storage/blobs/) service as remote storage for large files.
Azure Functions serverless computing platform is taken as a basis for deploying Git LFS application.

![architecture](https://app.lucidchart.com/publicSegments/view/05177de0-ae70-49fb-9510-f724562a68c6/image.png)

When user push/pull (1) changes Git LFS client make Batch API request (2) over HTTPS and triggered Azure Function.
In function for each LFS object generated (3) shared access signature (SAS) URL for temporary write/read access to Azure Blob Storage.
After received (4) response Git LFS client make uploading (5) / downloading (6) objects to/from Azure Blob Storage using SAS URL.

## Usage

