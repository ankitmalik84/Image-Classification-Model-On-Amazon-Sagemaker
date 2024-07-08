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
