import base64
import datetime
import hashlib
import os
import uuid
from ecdsa import SigningKey, SECP256k1
from ecdsa.util import sigencode_der
from jose import jwt
from requests_toolbelt.sessions import BaseUrlSession


class TestEnv:
    def __init__(self, standalone=False):
        self.standalone = standalone
        self.client_token = os.environ.get('BLOCKSET_TOKEN')
        self.client_headers = {
            'Authorization': f'Bearer {self.client_token}',
        }
        self.init_user_params()

    def init_user_params(self):
        self.user_signing_key = SigningKey.generate(curve=SECP256k1)
        self.user_token = ''
        self.user_headers = {}

    @staticmethod
    def create_standalone():
        env = TestEnv(standalone=True)
        session = BaseUrlSession(base_url='https://api.blockset.com')
        setattr(env, 'client', session)
        return env

    def create_user(self):
        pub_key = self.user_signing_key.verifying_key.to_string(encoding='uncompressed')
        signing_string = hashlib.sha256(self.client_token.encode('utf8'))
        sig = self.user_signing_key.sign_digest_deterministic(
            digest=signing_string.digest(),
            hashfunc=hashlib.sha256,
            sigencode=sigencode_der
        )
        user_payload = {
            'pub_key': base64.b64encode(pub_key).decode('utf8'),
            'signature': base64.b64encode(sig).decode('utf8'),
            'device_id': str(uuid.uuid4())
        }
        client = getattr(self, 'client')
        extra_kw = {}
        if not self.standalone:
            extra_kw['name'] = 'create_user'
        user_response = client.post(
            '/users/token',
            json=user_payload,
            headers=self.client_headers,
            **extra_kw
        ).json()
        self.user_token = jwt.encode({
            'brd:ct': 'usr',
            'brd:cli': user_response['client_token'],
            'sub': user_response['token'],
            'exp': datetime.datetime.now() + datetime.timedelta(days=1),
            'iat': datetime.datetime.now()
        }, self.user_signing_key, algorithm='ES256')
        self.user_headers = {
            'Authorization': f'Bearer {self.user_token}',
        }

    def delete_user(self):
        client = getattr(self, 'client')
        resp = client.delete('/users/me', headers=self.client_headers)
        if resp.status_code == 204:
            self.init_user_params()
