"""Live expand test: python -m tests.test_pybeoplay_expand SOURCE_HOST LISTENER_HOST."""
import argparse
import sys
import time

import requests

from pybeoplay import BeoPlay
from pybeoplay.const import BASE_URL, BEOPLAY_URL_ACTIVE_SOURCES, TIMEOUT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_host', help='Device hosting the current experience')
    parser.add_argument('listener_host', help='Device to add as a listener')
    args = parser.parse_args()

    try:
        response = requests.get(
            BASE_URL.format(args.listener_host, 'BeoDevice'), timeout=TIMEOUT
        )
        response.raise_for_status()
        jid = response.headers.get('Device-Jid')
        if not jid:
            product = response.json()['beoDevice']['productId']
            jid = '{}.{}.{}@products.bang-olufsen.com'.format(
                product['typeNumber'], product['itemNumber'], product['serialNumber']
            )
        device = BeoPlay(args.source_host)
        device.getSource()
        if not device.source:
            print('FAIL: Source device has no active experience.', file=sys.stderr)
            return 1
        print('Source:', args.source_host, device.source)
        print('Listener JID:', jid)
        print('Listeners before:', device.listeners)
        if not device.expand(jid):
            print('FAIL: Expand request was rejected or failed.', file=sys.stderr)
            return 1
        print('Expand request accepted.')
        for _ in range(10):
            device.getSource()
            if jid in device.listeners:
                print('PASS: Listener confirmed in source experience:', device.listeners)
                return 0
            time.sleep(1)
        # Include the listener state to help diagnose asynchronous or device failures.
        response = requests.get(
            BASE_URL.format(args.listener_host, BEOPLAY_URL_ACTIVE_SOURCES),
            timeout=TIMEOUT,
        )
        print('Listener active sources:', response.status_code, response.text)
        print('FAIL: Listener not confirmed within 10 seconds.', file=sys.stderr)
        return 1
    except (requests.RequestException, KeyError, ValueError) as exc:
        print('FAIL:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
