
import traceback
from datetime import date, datetime, timedelta
import json
import logging
import warnings

from yfinance.exceptions import YFRateLimitError
from finsim.data import get_yahoofinance_data


default_indices = {
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ Composite',
    '^DJI': 'Dow-Jones Industrial Average',
    '^RUT': 'Russell 2000',
    '^VIX': 'CBOE Voltaility Index'
}


def get_recent_indices(index, numdays=30, mockedtoday=None):
    todaystr = datetime.strftime(date.today(), '%Y-%m-%d') if mockedtoday is None else mockedtoday
    begindate = datetime.strftime(date.today()-timedelta(days=numdays), '%Y-%m-%d') if mockedtoday is None else datetime.strftime(datetime.strptime(todaystr, '%Y-%m-%d')-timedelta(days=numdays), '%Y-%m-%d')
    try:
        df = get_yahoofinance_data(index, begindate, todaystr)
    except YFRateLimitError:
        warnings.warn("Limit requests exceeded!")
        traceback.print_exc()
        return {}
    try:
        todayclosing = df[df['Date'] == todaystr]['Close'].to_numpy()[0]
    except KeyError:
        return {}
    except IndexError:
        return {}

    previousdaystr = datetime.strftime(df.iloc[-2, :].TimeStamp, '%Y-%m-%d')
    previousdayclosing = df[df['Date'] == previousdaystr]['Close'].to_numpy()[0]
    return {
        'today': {'date': todaystr, 'close': todayclosing},
        'previousday': {'date': previousdaystr, 'close': previousdayclosing}
    }


def lambda_handler(event, context):
    # mock today
    query = json.loads(event['body'])
    logging.info(query)
    print(query)
    mockedtoday = query.get('mockedtoday')
    indices = query.get('indices_to_show', default_indices)

    report_info = []
    for idxsymbol, idxname in indices.items():
        print('{}: {}'.format(idxsymbol, idxname))
        report_info.append({
            'index': idxsymbol,
            'name': idxname,
            'recent_values': get_recent_indices(idxsymbol, mockedtoday=mockedtoday)
        })
    logging.info(report_info)
    print(report_info)

    return {
        'statusCode': 200,
        'body': json.dumps(report_info)
    }