
import re
import os
import json
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
import asyncio

import boto3
import botocore
from dotenv import load_dotenv
import requests


load_dotenv()

# get userdb S3 bucket
s3_bucket = os.environ.get('BUCKET')

# telegram notififier Lambda ARN
finport_notifier_arn = os.environ.get('NOTIFIERARN')

# plotting API
maplotinfo_api_url = os.getenv('MAPLOT')


def send_telegram_picture(chatid, url):
    payload = {'body': {
        'chatid': chatid,
        'content': {
            'type': 'picture',
            'url': url
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


async def get_ma_plots_info(symbol, startdate, enddate, dayswindow, api_url, title=None):
    payload = json.dumps({
        'symbol': symbol,
        'startdate': startdate,
        'enddate': enddate,
        'dayswindow': dayswindow,
        'title': symbol if title is None else title
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", api_url, headers=headers, data=payload)
    return json.loads(response.text)


def lambda_handler(events, context):
    # get query
    query = json.loads(events)['body']
    logging.info(query)
    print(query)

    # get mockedtoday
    mockedtoday = query.get('mockedtoday')
    test = query.get('test', False)

    # get S&P 500 moving averages
    enddate = date.today().strftime('%Y-%m-%d')
    startdate = (date.today() - relativedelta(years=1)).strftime('%Y-%m-%d')
    plot_info = asyncio.run(
        get_ma_plots_info(
            '^GSPC',
            startdate,
            enddate,
            [50, 200],
            maplotinfo_api_url,
            title='S&P 500 ({})'.format(enddate)
        )
    )
    picurl = plot_info['plot']['url']

    # send notification
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
            send_telegram_picture(chatid, picurl)

    # return codes
    return {
        'statusCode': 200,
        'body': 'Picture sent. URL: {}'.format(picurl)
    }
