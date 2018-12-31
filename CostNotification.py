import os
import json
import boto3
import requests
from datetime import datetime, timedelta


class Time:
    start = ''
    end = ''


class Cost:
    each_service = []
    today_all = 0


def post_slack():
    TOKEN = os.environ['SLACK_ACCESS_TOKEN']
    CHANNEL = 'aws-estimate'
    URL = 'https://slack.com/api/chat.postMessage'

    post_json = {
        'token': TOKEN,
        'channel': CHANNEL,
        'attachments': json.dumps([
            {
                'pretext': Time.end + 'の料金: ' + '{0:.3f}'.format(Cost.today_all) + 'USD',
                'color': '#fdb407',
                'fields': Cost.each_service
            }
        ])
    }
    print(Cost.each_service)
    requests.post(URL, data=post_json)


def get_usage_service_and_cost(response):
    result_by_time = response['ResultsByTime'][0]
    groups = result_by_time['Groups']

    for service_group in groups:
        service = service_group['Keys'][0]
        amount = service_group['Metrics']['UnblendedCost']['Amount']

        # パースした内容をSlackの内容に合わせる
        service_and_cost_dict = {}
        service_and_cost_dict['title'] = service
        service_and_cost_dict['value'] = amount + 'USD'
        service_and_cost_dict['short'] = 1
        Cost.each_service.append(service_and_cost_dict)
        # 本日の料金合計を代入する
        Cost.today_all += float(amount)


def get_start_end_time():
    Time.start = (datetime.now() + timedelta(days=-2)).strftime('%Y-%m-%d')
    Time.end = (datetime.now() + timedelta(days=-1)).strftime('%Y-%m-%d')


def main(event, context):
    client = boto3.client('ce')
    # 開始期間と終了期間を取得
    get_start_end_time()

    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': Time.start,
            'End': Time.end
        },
        Granularity='DAILY',
        Metrics=[
            'UnblendedCost',
        ],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            },
        ]
    )

    get_usage_service_and_cost(response)
    post_slack()

    return response
