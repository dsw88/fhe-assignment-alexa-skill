#!/bin/bash -xe

#pip install -r requirements.txt -t .
aws cloudformation package --template-file sam_pre.yml --output-template-file sam_post.yml --s3-bucket byu-us-east-1-fhe-assignment-alexa-skill --profile devstg-us-east-1
aws cloudformation deploy --template-file sam_post.yml --stack-name fhe-alexa-skill --capabilities CAPABILITY_IAM --profile devstg-us-east-1
