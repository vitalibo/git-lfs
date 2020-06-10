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

### Self-Hosted

Module self-hosted allows you to use external hard driver for storing large files.
Module use Docker + Flask web-server for deploying service on the self-managed server, also you can run service locally.

![architecture](https://app.lucidchart.com/publicSegments/view/aec92441-cb88-4283-a359-2402b786e5b1/image.png)

When user push/pull (1) changes Git LFS client make Batch API request (2) over HTTP(S) to batch endpoint.
This endpoint return (3) transfer api endpoint for write/read access for each lfs object.
After receiving the response client make a request (4) to transfer endpoint, that redirect write/read (5) request to external hard drive and response returned back (6) to a client.

## Instructions

### Deploy

The deployment of Git LFS is fully based on terraform templates.
First of all you will need to install [terraform client](https://learn.hashicorp.com/terraform/getting-started/install.html).
To deploy Git LFS server you need go to `infrastructure` folder and invoke the appropriate commands for your infrastructure provider.

#### AWS

To get started with AWS you need to create an [AWS account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/) and configure [AWS cli](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html).

```bash
aws configure --profile default
```

After these steps you need create `aws/vars/<name>.tfvars` file with correct for you input variables.
Now you ready to create necessary resources, please invoke following command.

```bash
make apply provider=aws environment=dev profile=default auto-approve=true
```

After successful deployment output property `api_gateway_endpoint` contains your Git LFS server endpoint URL.

#### Azure

To get started with Azure you need to create an [Azure account](https://docs.microsoft.com/en-us/learn/modules/create-an-azure-account/) and configure [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).

```bash
az login
```

After these steps you need create `azure/vars/<name>.tfvars` file with correct for you input variables.
Now you ready to create necessary resources, please invoke following command.

```bash
make apply provider=azure environment=dev subscription_id=b4a47026-a2bd-11ea-bb37-0242ac130002 auto-approve=true
```

After successful deployment output property `function_app_endpoint` contains your Git LFS server endpoint URL.

#### Self-Hosted

To get started with self-hosted you need to install [Docker](https://docs.docker.com/get-docker/) engine.
After that you need create `aws/vars/<name>.tfvars` file with correct for you input variables.
Now you ready to create necessary resources, please invoke following command.

```bash
make apply provider=self environment=dev auto-approve=true
```
After successful deployment output property `endpoint` contains your Git LFS server endpoint URL.

### Usage

To use custom a Git LFS server you need perform steps described in a section [deploy](#Deploy).

Create `.lfsconfig` file in the root of your project repository and replace the endpoint url with correct for you value (see terraform output of deploying infrastructure).

```
[lfs]
url = htts://example.gitlfs.com/api/v1/
```

To associate a file type with Git LFS server, create `.gitattributes` in the root of your project repository and add your types as shown in the below example.

```
*.pdf filter=lfs diff=lfs merge=lfs -text
```

Commit `.lfsconfig` and `.gitattributes` files and push it to origin.

```bash
git add .lfsconfig .gitattributes
git commit -m 'Configure Git LFS server'
git push origin
``` 

Now you are ready to use Git LFS custom server.
To test it, commit `progit.pdf` binary file.

```bash
git add progit.pdf
git commit -m 'Add book Pro Git [Scott Chacon, Ben Straub]'
git push origin
```

After a successful commit, clone project to another location or another computer to confirm you can read the files.

All steps described here available in example that located in the `integration` folder.
