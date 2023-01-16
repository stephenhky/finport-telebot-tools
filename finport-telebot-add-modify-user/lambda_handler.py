
import json
import logging
import os

import boto3
import botocore


def lambda_handler(events, context):
    # get message
    user_info_input = events
    logging.info(user_info_input)
    print(user_info_input)

    # extract user information
    user_info = {
        'id': user_info_input['id'],
        'first_name': user_info_input['first_name'],
        'last_name': user_info_input.get('last_name'),
        'username': user_info_input['username']
    }

    # check if S3 has this profile
    s3_bucket = os.environ.get('BUCKET')
    s3_client = boto3.client('s3', 'us-east-1', config=botocore.config.Config(s3={'addressing_style': 'path'}))
    userfilename = 'tele-{}.json'.format(user_info['id'])
    # check if the file is there
    objects_retrieved = s3_client.list_objects(Bucket=s3_bucket, Prefix=userfilename)
    if 'Contents' in objects_retrieved:
        objectlist = objects_retrieved['Contents']
        objectlist = [object['Key'] for object in objectlist]
    else:
        objectlist = []
    if userfilename in objectlist:
        s3_client.download_file(
            s3_bucket,
            userfilename,
            os.path.join('/', 'tmp', userfilename)
        )
        existing_info = json.load(open(os.path.join('/', 'tmp', userfilename), 'r'))
        changed = False
        for key in ['id', 'first_name', 'last_name', 'username']:
            if user_info[key] != existing_info[key]:
                changed = True
                break
        if changed:
            logging.info('Changed record')
            print('Changed record')
            user_info['watchlists'] = existing_info['watchlists']
            json.dump(user_info, open(os.path.join('/', 'tmp', userfilename), 'w'))
            s3_client.upload_file(
                os.path.join('/', 'tmp', userfilename),
                s3_bucket,
                userfilename
            )
        else:
            logging.info('No action taken.')
            print('No action taken.')
    else:
        logging.info('Created record')
        print('Created record')
        user_info['watchlists'] = {}
        json.dump(user_info, open(os.path.join('/', 'tmp', userfilename), 'w'))
        s3_client.upload_file(
            os.path.join('/', 'tmp', userfilename),
            s3_bucket,
            userfilename
        )

    return {
        'statusCode': 200,
        'body': 'User created or changed.'
    }
