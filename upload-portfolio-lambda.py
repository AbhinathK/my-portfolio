import json
import boto3
import io
import zipfile
import mimetypes

def lambda_handler(event, context):

    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:542904164044:deployPortfolioTopic')

    location = {
        "bucketName": 'buildabhinathkumar.com',
        "objectKey": 'portfoliobuild.zip'
    }

    try:
        job = event.get('CodePipeline.job')
        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "BuildArtifact":
                    location = artifact["location"]["s3Location"]

        print("Building portfolio from " + str(location))

        s3 = boto3.resource("s3")

        portfolio_bucket = s3.Bucket('abhinathkumar.com')
        build_bucket = s3.Bucket(location["bucketName"])

        portfolio_zip = io.BytesIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj,nm,
                ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]} )
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')


        topic.publish(Subject='Portfolio Deployed', Message = 'Portfolio deployed succesfully')
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job["id"])

        return {
            'statusCode': 200,
            'body': json.dumps('Upload complete')
        }

    except:
        topic.publish(Subject='Portfolio Deploy Failed', Message='Portfolio deployment unsuccesful')
        raise
