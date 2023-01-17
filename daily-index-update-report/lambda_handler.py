
from datetime import date, datetime, timedelta
import json
import logging

from finsim.data import get_yahoofinance_data


indices = {
    '^DJI': 'Dow-Jones Industrial Average',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ Composite',
    '^VIX': 'CBOE Voltaility Index',
    '^RUT': 'Russell 2000'
}


def get_recent_indices(index, numdays=30, mockedtoday=None):
    todaystr = datetime.strftime(date.today(), '%Y-%m-%d') if mockedtoday is None else mockedtoday
    begindate = datetime.strftime(date.today()-timedelta(days=numdays), '%Y-%m-%d') if mockedtoday is None else datetime.strftime(datetime.strptime(todaystr, '%Y-%m-%d')-timedelta(days=numdays), '%Y-%m-%d')
    df = get_yahoofinance_data(index, begindate, todaystr)
    try:
        todayclosing = df.loc[todaystr, 'Close']
    except KeyError:
        return {}

    previousdaystr = datetime.strftime(df.iloc[-2, :].TimeStamp, '%Y-%m-%d')
    previousdayclosing = df.loc[previousdaystr, 'Close']
    return {
        'today': {'date': todaystr, 'close': todayclosing},
        'previousday': {'date': previousdaystr, 'close': previousdayclosing}
    }


def lambda_handler(event, context):
    # mock today
    query = json.loads(event['body'])
    logging.info(query)
    print(query)
    if 'mockedtoday' in query:
        mockedtoday = query['mockedtoday']
    else:
        mockedtoday = None

    report_info = []
    for idxsymbol, idxname in indices.items():
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