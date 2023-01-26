
import json
import logging
import os
from operator import itemgetter
import asyncio

import requests
from dotenv import load_dotenv
import telebot


logging.basicConfig(level=logging.INFO)

load_dotenv()

# Telebot API Key
api_key = os.getenv('APIKEY')
bot = telebot.TeleBot(api_key, threaded=False)

# Search API
search_api_url = os.getenv('SEARCH')
modelloadretry = int(os.getenv('MODELLOADRETRY', 5))


async def search_symbols(querystring, api_url):
    payload = json.dumps({'querystring': querystring, 'topn': 6})
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request('GET', api_url, headers=headers, data=payload)
    return json.loads(response.text)


def lambda_handler(event, context):
    logging.info(event)
    print(event)
    # getting message
    message = telebot.types.Message.de_json(event)
    logging.info(message)
    print(message)

    querystring = message.text[8:].strip()
    logging.info('query string: {}'.format(querystring))
    print('query string: {}'.format(querystring))
    for i in range(modelloadretry):
        results = asyncio.run(search_symbols(querystring, search_api_url))
        if 'message' in results and 'timed out' in results['message']:
            logging.info('Trial {} fail'.format(i))
            print('Trial {} fail'.format(i))
            bot.reply_to(message, 'Model loading...')
        elif 'queryresults' in results:
            break
        else:
            logging.info('Trial {} fail with error'.format(i))
            print('Trial {} fail with error'.format(i))
            bot.reply_to(message, 'Unknown error; retrying...')
    logging.info(results)
    print(results)
    if 'queryresults' not in results:
        bot.reply_to(message, 'Unknown error.')
        return {
            'statusCode': 500,
            'body': 'Unknown error'
        }
    else:
        symbol_and_descp = [
            symbolprob['symbol'] + ' : ' + symbolprob['descp']
            for symbolprob in sorted(results['queryresults'], key=itemgetter('prob'), reverse=True)
        ]
        bot.reply_to(message, '\n'.join(symbol_and_descp))
        return {
            'statusCode': 200,
            'body': json.dumps({
                'searchresults': sorted(results['queryresults'], key=itemgetter('prob'), reverse=True),
                'message': '\n'.join(symbol_and_descp)
            })
        }
