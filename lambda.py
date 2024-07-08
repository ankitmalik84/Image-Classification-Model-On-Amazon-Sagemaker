""" 
    The first lambda function is responsible for data generation.
    SerializeImageData:
    A lambda function that copies an object from S3, base64 encodes it, and 
    then return it (serialized data) to the step function as `image_data` in an event.
"""

import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the s3 address from the Step Function event input
    key = event["s3_key"]
    bucket = event["s3_bucket"]
    
    # Download the data from s3 to /tmp/image.png
    boto3.resource('s3').Bucket(bucket).download_file(key, "/tmp/image.png")
    
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }


""" 
    The second one is responsible for image classification.
    It takes the image output from the lambda 1 function(SerializeImageData), decodes it, and then pass inferences back to the the Step Function.
"""
import json
import sagemaker
import base64
from sagemaker.serializers import IdentitySerializer

# Fill this in with the name of your deployed model
ENDPOINT = "image-classification-2024-07-07-12-53-17-472"

# # We will be using the AWS's lightweight runtime solution to invoke an endpoint.
runtime= boto3.client('runtime.sagemaker')

def lambda_handler(event, context):

    # Decode the image data
    image = base64.b64decode(event["body"]["image_data"])

    # Instantiate a Predictor
    predictor = runtime.invoke_endpoint(
                                        EndpointName=ENDPOINT,
                                        ContentType='application/x-image',
                                        Body=image
                                        )
    
    # Read and decode the prediction result
    inferences = json.loads(predictor['Body'].read().decode('utf-8'))
    
    # Add the inferences to the event
    event["inferences"] = inferences
    
    return {
        'statusCode': 200,
        'body': {
            "image_data": event["body"]['image_data'],
            "s3_bucket": event["body"]['s3_bucket'],
            "s3_key": event["body"]['s3_key'],
            "inferences": event['inferences'],
       }
    }

""" 
    The third function is responsible for filtering out low-confidence inferences.
    It takes the inferences from the Lambda 2 function output and filters low-confidence inferences
    above a certain threshold indicating success"
"""
import json


THRESHOLD = .93


def lambda_handler(event, context):
    
    # Grab the inferences from the event
    inferences = event['data']['inferences']
    
    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = (max(inferences)>THRESHOLD)
    
    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
