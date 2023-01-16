
import re
import os
import json
import logging
from datetime import date, datetime

import boto3
import botocore
from dotenv import load_dotenv
import requests


load_dotenv()

# get daily report computation API
DAILYREPORT_API_URL = os.environ.get('DAILYREPORTAPI')

# get userdb S3 bucket
s3_bucket = os.environ.get('BUCKET')

# telegram notififier Lambda ARN
finport_notifier_arn = os.environ.get('NOTIFIERARN')


def send_telegram_text_notification(chatid, text):
    payload = {'body': {
        'chatid': chatid,
        'content': {
            'type': 'text',
            'message': text
        }
    }}
    logging.info(payload)
    print(payload)

    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=finport_notifier_arn,
        InvocationType='Event',
        Payload=json.dumps(payload)
    )


def lambda_handler(events, context):
    # get query
    query = json.loads(events)['body']
    logging.info(query)
    print(query)

    # get mockedtoday
    mockedtoday = query.get('mockedtoday')
    test = query.get('test', False)

    # get daily computation reports
    response = requests.request(
        "GET",
        DAILYREPORT_API_URL,
        headers={
            'Content-Type': 'application/json'
        },
        data=json.dumps({'mockedtoday': mockedtoday})
    )
    report_dict = json.loads(response.text)

    # generate reports
    report_str = '{} {}\n'.format(datetime.strftime(date.today(), '%Y-%m-%d'), '(TEST)' if test else '')
    for index_info in report_dict:
        values = index_info['recent_values']
        if len(values) > 0:
            this_index_str = '{} ({})\n'.format(index_info['name'], index_info['index'])
            this_index_str += '  {:.2f} ({} by {:.2f}% from {} ({:.2f})\n'.format(
                values['today']['close'],
                'increase' if values['today']['close'] >= values['previousday']['close'] else 'decrease',
                abs((values['today']['close']-values['previousday']['close']) / values['today']['close'] * 100),
                values['previousday']['date'],
                values['previousday']['close']
            )
            report_str += this_index_str
    logging.info(report_str)
    print(report_str)

    # send out notification
    s3_client = boto3.client('s3', 'us-east-1', config=botocore.config.Config(s3={'addressing_style': 'path'}))
    objects_retrieved = s3_client.list_objects(Bucket=s3_bucket)
    objectlist = objects_retrieved['Contents']
    objectlist = [object['Key'] for object in objectlist]
    logging.info(objectlist)
    print(objectlist)
    for userjsonname in objectlist:
        logging.info(userjsonname)
        print(userjsonname)
        matcher = re.match('tele-(\\d+)\.json', userjsonname)
        if matcher is not None:
            chatid = int(matcher.group(1))
            send_telegram_text_notification(chatid, report_str)

    # return codes
    return {
        'statusCode': 200,
        'body': 'Message sent: {}'.format(report_str)
    }
