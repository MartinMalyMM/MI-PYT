import pytest
import betamax
import os
import requests
import sys
import filabel
from filabel import find_labels 
from filabel import find_pulls
from filabel import find_pull_files
from filabel import find_pull_labels
from click.testing import CliRunner
import configparser # for test_find_labels
import pathlib      # for test_find_labels
import json         # pick_username()

def test_no_config():
    runner = CliRunner()
    result = runner.invoke(filabel.main, [''])
    assert result.exit_code == 1
    assert 'Auth configuration not supplied!' in result.output

with betamax.Betamax.configure() as config:
    # tell Betamax where to find the cassettes
    # make sure to create the directory
    config.cassette_library_dir = 'tests/fixtures/cassettes'
    
    if 'GH_TOKEN' in os.environ:
        # If the tests are invoked with an AUTH_FILE environ variable
        TOKEN = os.environ['GH_TOKEN']
        # Always re-record the cassetes
        # https://betamax.readthedocs.io/en/latest/record_modes.html
        config.default_cassette_options['record_mode'] = 'all'
    else:
        TOKEN = 'false_token'
        # Do not attempt to record sessions with bad fake token
        config.default_cassette_options['record_mode'] = 'none'

    # Hide the token in the cassettes
    config.define_cassette_placeholder('<TOKEN>', TOKEN)

@pytest.fixture
def client(betamax_parametrized_session):
    return Client(token=TOKEN, session=betamax_parametrized_session)
            
class Client:
    def __init__(self, token, session=None):
        self.session = self._create_session(token, session)
        
    def _create_session(self, token, session):
        session = session or requests.Session()
        session.headers = {'User-Agent': 'Python'}
        session.headers.update({'Accept-Encoding': 'identity'}) #new#
        def token_auth(req):
            req.headers['Authorization'] = f'token {token}'
            return req
        session.auth = token_auth
        return session
        
    def _get(self, url):
        r = self.session.get(url)
        return r
        
    def _username(self):
        r = self._get('https://api.github.com/user')
        username = r.json()['login']
        #print(username)
        return username
        
def test_client(client): 
    # Nahrát nebo spustit kazetu
    # client = Client(session=betamax_session) # Toto nyní obstarává @pytest.fixture client
    r = client._get('https://api.github.com/user')
    assert "200" in str(r.status_code), "Authentication at GitHub was not succesful. Is the token saved in $GH_TOKEN OK?"
    os.environ["GH_USER"] = r.json()['login']
    #assert username = username_loc
    

def config(name):
    return pathlib.Path(__file__).parent / 'fixtures' / name

def pick_username(): # Dost prasárna...
    try:
        with open(pathlib.Path(__file__).parent / 'fixtures' / 'cassettes' / 'test_github_clean.test_client.json', 'r') as c:
            cassette = json.load(c)
        dic = str(cassette["http_interactions"][0]["response"])
        dic_ = dic.split('\"')
        username = dic_[3]
    except FileNotFoundError:
        username = os.environ['GH_USER']
    return username
    
def test_username():
    username = pick_username()
    assert username
    
username = pick_username()


labels_normal_array = """[['frontend', ['*/templates/*', 'static/*']], ['backend', ['logic/*']], ['docs', ['*.md', '*.rst', '*.adoc', 'LICENSE', 'docs/*']]]"""
labels_xyz_array = """[['x', ['x*']], ['xy', ['x*', 'y*']], ['xyz', ['x*', 'y*', 'z*']], ['p', ['p*']]]"""
@pytest.mark.parametrize(
    ["cfg", "labels_str"],
    [("labels_normal.cfg", labels_normal_array),
     ("labels_xyz.cfg", labels_xyz_array)],
    ids=["labels_normal.cfg", "labels_xyz.cfg"]
)
def test_find_labels(cfg, labels_str):
    config_labels = config(cfg)
    with open(config_labels, "r") as f:
        config_labels_string = f.read()
    labels_parser = configparser.ConfigParser()
    labels_parser.read_string(str(config_labels_string))
    labels = find_labels(labels_parser)
    assert labels
    assert str(labels) == labels_str
    return labels
    

@pytest.mark.parametrize(
    ["repo", "base", "state", "number"],
    [("filabel-testrepo1", "master", "all", 2),
     ("filabel-testrepo1", "master", "open", 2),
     ("filabel-testrepo1", "master", "closed", 0),
     ("filabel-testrepo1", "pr1", "all", 0),
     ("filabel-testrepo1", "pr2", "all", 0), 
     ##
     ("filabel-testrepo2", "master", "all", 111),
     ("filabel-testrepo2", "pr110", "all", 0),
     ##
     ("filabel-testrepo3", "master", "all", 0),
     ##
     ("filabel-testrepo4", "master", "all", 2),
     ("filabel-testrepo4", "master", "open", 1),
     ("filabel-testrepo4", "master", "closed", 1),
     #
     ("filabel-testrepo4", "pr_open", "all", 1),
     ("filabel-testrepo4", "pr_open", "open", 1),
     ("filabel-testrepo4", "pr_open", "closed", 0),
     #
     ("filabel-testrepo4", "pr_closed", "all", 0),
     ("filabel-testrepo4", "pr_closed", "open", 0),
     ("filabel-testrepo4", "pr_closed", "closed", 0),
     #
     ("filabel-testrepo4", "pr2pr", "all", 0),
     ("filabel-testrepo4", "pr2pr", "open", 0),
     ("filabel-testrepo4", "pr2pr", "closed", 0)]
)
def test_find_pulls(client, betamax_parametrized_session, repo, base, state, number):
    pulls = find_pulls(betamax_parametrized_session, username + "/" + repo, base, state)
    #print(str(pulls))
    assert len(pulls) == number
    return pulls
    
@pytest.mark.parametrize(
    ["repo", "pull", "files"],
    [("filabel-testrepo1", 1, ['aaaa', 'bbbb', 'cccc', 'dddd']),
     ("filabel-testrepo2", 1, ['radioactive', 'waste']),
     ("filabel-testrepo2", 9, ['radioactive', 'waste']),
     ("filabel-testrepo2", 99, ['radioactive', 'waste']),
     ("filabel-testrepo2", 111, ['radioactive', 'waste']),
     ("filabel-testrepo4", 1, ['aaaa']),
     ("filabel-testrepo4", 2, ['aaaa']),
     ("filabel-testrepo4", 3, ['bbbb'])]
)    
def test_find_pull_files_(client, betamax_parametrized_session, repo, pull, files):
    pull_files = find_pull_files(betamax_parametrized_session, username + "/" + repo, pull)
    assert pull_files == files       

def test_find_pull_files_222(client, betamax_parametrized_session, repo="filabel-testrepo1", pull=2):
    #username = client._username()
    files_list_222 = []
    for i in range(222):
        files_list_222.append("file" + str(i+1))
    pull_files = find_pull_files(betamax_parametrized_session, username + "/" + repo, pull)
    assert len(pull_files) == len(files_list_222)
    n_files = 0
    for a in pull_files:
        for b in files_list_222:
            if a == b:
                n_files = n_files + 1
    assert n_files == len(files_list_222)

@pytest.mark.parametrize(
    ["repo", "pull"],
    [("filabel-testrepo1", 1),
     ("filabel-testrepo1", 2),
     ("filabel-testrepo2", 1),
     ("filabel-testrepo2", 9),
     ("filabel-testrepo2", 99),
     ("filabel-testrepo2", 111),
     ("filabel-testrepo4", 1),
     ("filabel-testrepo4", 2),
     ("filabel-testrepo4", 3)]
)
def test_find_pull_labels(client, betamax_parametrized_session, repo, pull):
    labels = test_find_labels("labels_normal.cfg", labels_normal_array)
    pull_labels_i = find_pull_labels(betamax_parametrized_session, username + "/" + repo, pull, labels)
    assert not pull_labels_i
