import random
from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
from lib import TestEnv

IGNORE_ADDRESSES = {'fee', '__fee__', 'coinbase', 'unknown'}


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class QuickstartUser(FastHttpUser, TestEnv):
    wait_time = between(0.5, 2)

    def on_start(self):
        """create user"""
        self.create_user()

    def on_stop(self):
        """delete user"""
        pass

    @task
    def get_blockchains_client(self):
        self.client.get(
            '/blockchains',
            headers=self.client_headers,
            name='get_blockchains_client'
        )

    @task
    def get_blockchains_user(self):
        self.client.get(
            '/blockchains',
            headers=self.user_headers,
            name='get_blockchains_user'
        )

    @task
    def get_blockchains_testnet_client(self):
        self.client.get(
            '/blockchains?testnet=true',
            headers=self.client_headers,
            name='get_blockchains_testnet_client'
        )

    @task
    def get_blockchains_testnet_client(self):
        self.client.get(
            '/blockchains?testnet=true',
            headers=self.user_headers,
            name='get_blockchains_testnet_user'
        )

    @task
    def get_verified_currencies_client(self):
        self.client.get(
            '/currencies?verified=true',
            headers=self.client_headers,
            name='get_verified_currencies_client'
        )

    @task
    def get_verified_currencies_user(self):
        self.client.get(
            '/currencies?verified=true',
            headers=self.user_headers,
            name='get_verified_currencies_user'
        )

    @task
    def sync_bitcoin_mainnet_random_wallet_user(self):
        # get the most recent block hash
        chain = self.client.get(
            '/blockchains/bitcoin-mainnet',
            name='/blockchains/[id]',
            headers=self.client_headers
        ).json()
        # fetch the block
        block = self.client.get(
            f'/blocks/bitcoin-mainnet:{chain["verified_block_hash"]}',
            name='/blocks/[id]',
            headers=self.client_headers
        ).json()
        # fetch 100 random transactions and capture at least 500 addresses
        addresses = []
        for i in range(100):
            txid = random.choice(block['transaction_ids'])
            transaction = self.client.get(
                f'/transactions/bitcoin-mainnet:{txid}',
                name='/transactions/[id]',
                headers=self.client_headers,
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
                headers=self.client_headers
            ).json()



