import json
import boto3
import os
from boto3.dynamodb.conditions import Attr

def handler(event, context):
    dynamodb = boto3.resource('dynamodb')

    # When removing portfolios, we need to remove apps and zones for the portfolio

    apps_table = dynamodb.Table(os.environ['APPS_TABLE'])
    zones_table = dynamodb.Table(os.environ['ZONES_TABLE'])

    log_level = os.environ.get('LOG_LEVEL', 'ERROR').upper()

    try:
        count = 0
        for record in event['Records']:
            if record['eventName'] == 'REMOVE':
                client = record['dynamodb']['OldImage']['Client']['S']
                portfolio = record['dynamodb']['OldImage']['Portfolio']['S']

                portfolio_facts = f'{client}:{portfolio}'

                response = apps_table.scan(
                    FilterExpression=Attr('ClientPortfolio').eq(portfolio_facts)
                )

                for item in response['Items']:
                    app_regex = item['AppRegex']
                    apps_table.delete_item(
                        Key={
                            'ClientPortfolio': portfolio_facts,
                            'AppRegex': app_regex
                        }
                    )
                    count += 1
                    if log_level == 'INFO':
                        print(f'SUCCESS: [{portfolio_facts}], AppRegex [{app_regex}] deleted')

                response = zones_table.scan(
                    FilterExpression=Attr('ClientPortfolio').eq(portfolio_facts)
                )

                for item in response['Items']:
                    zone = item['Zone']
                    zones_table.delete_item(
                        Key={
                            'ClientPortfolio': portfolio_facts,
                            'Zone': zone
                        }
                    )
                    count += 1
                    if log_level == 'INFO':
                        print(f'SUCCESS: [{portfolio_facts}], zone [{zone}] deleted')

                count += 1
                if log_level == 'INFO':
                    print(f'SUCCESS: [{portfolio_facts}] deleted')

        print(f'SUCCESS: {count} records deleted')
        return {
            'statusCode': 200,
            'body': json.dumps(f'Success: {len(event["Records"])} events deleted')  # Should be {count}
        }
    except Exception as e:
        print(f'ERROR: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
