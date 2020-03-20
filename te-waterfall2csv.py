import argparse
import csv
import os
import requests
from urllib.parse import urlparse


class ThousandEyesWaterfallToCsv(object):
    def __init__(self):
        parser = argparse.ArgumentParser(prog='te-waterfall2csv.py')
        parser.add_argument(
            '--token',
            help="ThousandEyes OAuth Bearer Token. Defaults to environment THOUSANDEYES_OAUTH_TOKEN",
            default=os.environ.get('THOUSANDEYES_OAUTH_TOKEN', None)
        )

        subparsers = parser.add_subparsers(help='')

        parser_getcsv = subparsers.add_parser('getcsv', help='Download waterfall data as a CSV file')
        parser_getcsv.add_argument('test', type=int, help="Test ID")
        parser_getcsv.add_argument('agent', type=int, help='Agent ID')
        parser_getcsv.add_argument('round', type=int, help='Round ID')
        parser_getcsv.add_argument('outfile', help='Ouput CSV Filename')
        parser_getcsv.set_defaults(func=self.getcsv)

        parser_agentlist = subparsers.add_parser('agentlist', help='List the Agents assigned to a Test')
        parser_agentlist.add_argument('test', type=int, help="Test ID")
        parser_agentlist.set_defaults(func=self.agentlist)

        args = parser.parse_args()

        if args.token is None:
            parser.print_help()
            exit(2)
        else:
            self.token = args.token

        try:
            func = args.func
        except AttributeError:
            parser.print_help()
            exit(2)

        func(args)

    def getcsv(self, args):
        api_endpoint = f"https://api.thousandeyes.com/v7/web/page-load/{args.test}/{args.agent}/{args.round}.json"
        response = requests.get(
            api_endpoint,
            headers={
                'Authorization': 'Bearer' + self.token,
            }
        )

        if response.status_code == 200:
            response = response.json()
            test_data = response['web']['pageLoad'][0]
            har = test_data['har']
            with open(args.outfile, 'w') as f:
                csv_file = csv.writer(f)
                csv_file.writerow(['Agent', test_data['agentName']])
                csv_file.writerow(['Date', test_data['date']])
                csv_file.writerow(['Time to First Byte (ms)', test_data['responseTime']])
                csv_file.writerow(['DOM Load Time (ms)', test_data['domLoadTime']])
                csv_file.writerow(['Page Load Time (ms)', test_data['pageLoadTime']])
                csv_file.writerow(['Number of Objects', test_data['numObjects']])
                csv_file.writerow(['Total Page Size (bytes)', test_data['totalSize']])
                csv_file.writerow(['ThousandEyes URL', test_data['permalink']])
                csv_file.writerow([])
                csv_file.writerow([])
                csv_file.writerow([
                    'object',
                    'hostname',
                    'size (bytes)',
                    'startedDateTime',
                    'total time (ms)',
                    'blocked',
                    'dns',
                    'connect',
                    'ssl',
                    'send',
                    'wait',
                    'receive',
                    'mimetype',
                    'full url',
                ])
                for entry in har['log']['entries']:
                    parsed_url = urlparse(entry['request']['url'])
                    timings = entry['timings']
                    csv_file.writerow([
                        parsed_url.path.rsplit('/', 1)[-1] if parsed_url.path != '/' else '/',
                        parsed_url.hostname,
                        entry['response']['bodySize'],
                        entry['startedDateTime'],
                        entry['time'],
                        timings['blocked'],
                        timings['dns'],
                        timings['connect'],
                        timings['ssl'],
                        timings['send'],
                        timings['wait'],
                        timings['receive'],
                        entry['response']['content'].get('mimeType', '[unknown]'),
                        entry['request']['url'],
                    ])
        else:
            print(f"Received non-200 HTTP response: {response.status_code}")

    def agentlist(self, args):
        api_endpoint = f"https://api.thousandeyes.com/v7/tests/{args.test}.json"
        response = requests.get(
            api_endpoint,
            headers={
                'Authorization': 'Bearer' + self.token,
            }
        )
        if response.status_code == 200:
            test_details = response.json()['test'][0]
            for agent in test_details['agents']:
                print(f"ID: {agent['agentId']}\t\t : {agent['agentName']}")
        else:
            print(f"Received non-200 HTTP response: {response.status_code}")


if __name__ == '__main__':
    ThousandEyesWaterfallToCsv()
