#!/bin/bash -xe

#pip install -r requirements.txt -t .
aws cloudformation package --template-file sam_pre.yml --output-template-file sam_post.yml --s3-bucket appdev-infa-xfer --profile default
aws cloudformation deploy --template-file sam_post.yml --stack-name fhe-alexa-skill --capabilities CAPABILITY_IAM --profile default
