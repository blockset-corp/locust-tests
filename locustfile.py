import os
from locust import task
from locust.contrib.fasthttp import FastHttpUser


class QuickstartUser(FastHttpUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = os.environ.get('BLOCKSET_TOKEN')
        self.headers = {
            'authorization': f'Bearer {self.token}',
        }

    @task
    def get_blockchains(self):
        self.client.get('/blockchains', headers=self.headers)

    @task
    def get_blockchains_testnet(self):
        self.client.get('/blockchains?testnet=true', headers=self.headers)
