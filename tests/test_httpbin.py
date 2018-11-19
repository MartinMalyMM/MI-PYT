import pytest
import betamax
import os
import requests

with betamax.Betamax.configure() as config:
    # tell Betamax where to find the cassettes
    # make sure to create the directory
    config.cassette_library_dir = 'tests/fixtures/cassettes'

@pytest.fixture
def client(betamax_session):
    return Client(session=betamax_session)

class Client:
    def __init__(self, session=None):
        self.session = session or requests.Session()
        
def test_client(betamax_session):
    # Nahrát nebo sputit kazetu
    # client = Client(session=betamax_session) # Toto nyní obstarává @pytest.fixture client
    r = betamax_session.get('https://httpbin.org/get')
    assert "200" in str(r.status_code)
    # Co je na nahráté kazetě? (buď dříve nahraně nebo čerstvě nahrané)
    #print(r.json())
