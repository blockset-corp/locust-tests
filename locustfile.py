import os
import random
from locust import task, between
from locust.contrib.fasthttp import FastHttpUser

IGNORE_ADDRESSES = {'fee', '__fee__', 'coinbase', 'unknown'}


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class QuickstartUser(FastHttpUser):
    wait_time = between(0.5, 2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = os.environ.get('BLOCKSET_TOKEN')
        self.headers = {
            'authorization': f'Bearer {self.token}',
        }

    @task
    def get_blockchains(self):
        self.client.get(
            '/blockchains',
            headers=self.headers
        )

    @task
    def get_blockchains_testnet(self):
        self.client.get(
            '/blockchains?testnet=true',
            headers=self.headers
        )

    @task
    def get_verified_currencies(self):
        self.client.get(
            '/currencies?verified=true',
            headers=self.headers
        )

    @task
    def sync_bitcoin_mainnet_random_wallet(self):
        # get the most recent block hash
        chain = self.client.get(
            '/blockchains/bitcoin-mainnet',
            name='/blockchains/[id]',
            headers=self.headers
        ).json()
        # fetch the block
        block = self.client.get(
            f'/blocks/bitcoin-mainnet:{chain["verified_block_hash"]}',
            name='/blocks/[id]',
            headers=self.headers
        ).json()
        # fetch 100 random transactions and capture at least 500 addresses
        addresses = []
        for i in range(100):
            txid = random.choice(block['transaction_ids'])
            transaction = self.client.get(
                f'/transactions/bitcoin-mainnet:{txid}',
                name='/transactions/[id]',
                headers=self.headers
            ).json()
            for transfer in transaction['_embedded']['transfers']:
                if transfer['from_address'] not in IGNORE_ADDRESSES:
                    addresses.append(transfer['from_address'])
                if transfer['to_address'] not in IGNORE_ADDRESSES:
                    addresses.append(transfer['to_address'])
            if len(addresses) > 500:
                break
        # grab up to 500 addresses and "sync" them from block height - 10,000 blocks
        for address_sublist in chunks(addresses[:500], 25):
            query = '&address='.join(f'{a}' for a in address_sublist)
            start_height = chain['verified_height'] - 10_000
            end_height = chain['verified_height']
            # TODO: paginate the responses
            self.client.get(
                f'/transactions?blockchain_id=bitcoin-mainnet&max_page_size=100&start_height={start_height}&end_height={end_height}&address={query}',
                name='/transactions&address=[addr]',
                headers=self.headers
            ).json()
