import click
import configparser
import requests
import fnmatch
import sys
from flask import Flask, request, jsonify, abort
app = Flask(__name__)
from flask import render_template
import jinja2
import os
import hmac
import hashlib
import json

#Usage: filabel.py [OPTIONS] [REPOSLUGS]...
#
#  CLI tool for filename-pattern-based labeling of GitHub PRs
#
#Options:
#  -s, --state [open|closed|all]   Filter pulls by state.  [default: open]
#  -d, --delete-old / -D, --no-delete-old
#                                  Delete labels that do not match anymore.
#                                  [default: True]
#  -b, --base BRANCH               Filter pulls by base (PR target) branch
#                                  name.
#  -a, --config-auth FILENAME      File with authorization configuration.
#  -l, --config-labels FILENAME    File with labels configuration.
#  --help                          Show this message and exit.
  
@click.command()
@click.option('-s', '--state', type=click.Choice(['open', 'closed', 'all']),             
              default='open',
              help='Filter pulls by state.  [default: open]')
@click.option('-d/-D', '--delete-old/--no-delete-old', default=True,
              help='Delete labels that do not match anymore.  [default: True]')
              # variable name is delete_old, not delete-old
@click.option('-b', '--base', metavar='BRANCH',
              help='Filter pulls by base (PR target) branch name.')
@click.option('-a', '--config-auth', metavar='FILENAME',
              type=click.File('r'),
              help='File with authorization configuration.')              
@click.option('-l', '--config-labels', metavar='FILENAME',
              type=click.File('r'),
              help='File with labels configuration.')                  
@click.argument('reposlugs', nargs=-1)
# Přepínače --config-auth a --config-labels můžete nastavit jako povinné. 




def main(state, delete_old, base, config_auth, config_labels, reposlugs):
    """CLI tool for filename-pattern-based labeling of GitHub PRs"""

    # Check if authorization configuration is supplied
    config_parser = configparser.ConfigParser()
    if not config_auth: # set options to be obligatory?
        click.echo("Auth configuration not supplied!", err=True)
        sys.exit(1)

    # Check if labels configuration is supplied
    if not config_labels:    
        click.echo("Labels configuration not supplied!", err=True)
        sys.exit(1)

    # Check reposlugs validity 1/2
    for reposlug in reposlugs:
        if "/" in reposlug.split("/",maxsplit=1)[-1] or reposlug[0] == '/' or reposlug[-1] == '/' or not "/"  in reposlug:
            click.echo("Reposlug " + reposlug + " not valid!", err=True)
            sys.exit(1)           
    
    # Check usability of labels configuration
    labels_parser = configparser.ConfigParser()
    try:
        labels_parser.read_file(config_labels)
    except:
        click.echo("Labels configuration not usable!", err=True)
        sys.exit(1)
    try:
        labels_parser['labels']
    except:
        click.echo("Labels configuration not usable!", err=True)
        sys.exit(1)        
        
    # Check usability of authorization configuration
    try:
        config_parser.read_file(config_auth) # Token is now saved in config['github']['token']
    except:
        click.echo("Auth configuration not usable!", err=True)
        sys.exit(1)             
    try:
        token = config_parser['github']['token']
    except KeyError:
        click.echo("Auth configuration not usable!", err=True)
        sys.exit(1) 
    session = requests.Session()
    session.headers = {'User-Agent': 'Python'}
    def token_auth(req): # Why it is placed here?
        req.headers['Authorization'] = f'token {token}'
        return req
    session.auth = token_auth
    r = session.get('https://api.github.com/user')
    #r.json()
    if not "200" in str(r.status_code): #200
        #print(str(r.status_code))
        click.echo("Auth configuration not usable!", err=True)
        sys.exit(1)
    
    # Check reposlugs validity 1/2
    if not reposlugs:
        click.echo("No reposlug supplied!", err=True) # TODO
        sys.exit(1)    
    
    # Formating
    repo = click.style("REPO", bold=True)
    pr = click.style("  PR", bold=True)
    ok = click.style("OK", fg='green', bold=True)
    fail = click.style("FAIL", fg='red', bold=True)
        
    # Check reposlugs validity 2/2
    for reposlug in reposlugs:

        # List of labels
        labels_parser.read_file(config_labels)        
        labels = find_labels(labels_parser)
       

        # Find PRs in repository
        pulls = find_pulls(session, reposlug, base, state, repo, ok, fail)
        if not pulls:
            continue

    
        for pull in pulls:
            pull_error = False
            # Find files of particular PR
            pull_files = find_pull_files(session, reposlug, pull)
            
            # Find the current setting of labels of particular PR
            # All labels - "raw"
            pull_labels_i = find_pull_labels(session, reposlug, pull, labels)                           
            
            pull_labels_f = []
            # Make up the wished setting of label, taking labels.cfg into account
            for key in range(len(labels)):
                for fileset in range(len(labels[key][1])):
                    for f in pull_files:
                        if fnmatch.fnmatch(f, labels[key][1][fileset]):
                            print_debug("   This PR with file " + f + " should have label " + labels[key][0])
                            pull_labels_f.append(labels[key][0])
                            
            # Delete labels which do not match with configuration setting (if set by options)
            if delete_old:
                pull_labels_D = list(set(pull_labels_i)-set(pull_labels_f))
            else:
                pull_labels_D = []
            if pull_labels_D:
                print_debug("These labels will be deleted:")    # Check usability of labels configuration
                print_debug(pull_labels_D)
                for label in pull_labels_D:
                    r = session.delete('https://api.github.com/repos/' + reposlug + '/issues/' + str(pull) + '/labels/' + str(label))
                    print_debug(str(r.status_code))
                    if not "200" in str(r.status_code):
                        pull_error = True
                        break
                if pull_error:
                    click.echo('{}'.format(pr) + " https://github.com/" + reposlug + "/" + str(pull) + " - " + fail)
                    continue
            
            # Add labels
            pull_labels_A = list(set(pull_labels_f)-set(pull_labels_i))
            if pull_labels_A:
                print_debug("These labels will be added:")
                print_debug(pull_labels_A)                
                for label in pull_labels_A:
                    r = session.post('https://api.github.com/repos/' + reposlug + '/issues/' + str(pull) + '/labels', json = pull_labels_A)
                    print_debug(str(r.status_code))     
                    if not "200" in str(r.status_code):
                        pull_error = True
                        break
                if pull_error:
                    click.echo('{}'.format(pr) + " https://github.com/" + reposlug + "/pull/" + str(pull) + " - " + fail)
                    continue
            
            # Find what has not changed
            pull_labels_K = list(set(pull_labels_i) & set(pull_labels_f))            
            
            # Write results to output
            pull_labels_A_dict = {l: "+" for l in pull_labels_A}
            pull_labels_D_dict = {l: "-" for l in pull_labels_D}
            pull_labels_K_dict = {l: "=" for l in pull_labels_K}
            pull_labels_result = pull_labels_A_dict
            pull_labels_result.update(pull_labels_D_dict)
            pull_labels_result.update(pull_labels_K_dict)
            click.echo('{}'.format(pr) + " https://github.com/" + reposlug + "/pull/" + str(pull) + " - " + ok)
            for label, change in sorted(pull_labels_result.items()):
                if change == "+":
                    click.echo('{}'.format(click.style("    + " + label, fg='green')))
                elif change == "-":
                    click.echo('{}'.format(click.style("    - " + label, fg='red')))
                elif change == "=":
                    click.echo('{}'.format(click.style("    = " + label)))
            print_debug(pull_labels_result)                    
            print_debug("")    
    return



def find_labels(labels_parser):
    labels_parser.sections()    
    labels = []
    print_debug("Labels:")
    for key in labels_parser['labels']:
        print_debug(" - Label: " + key)
        key_array = []
        key_array.append(key)  
        labels_line = []      
        for label in labels_parser['labels'][key].splitlines():
            if label:
                print_debug("    - File: " + label)                
                labels_line.append(label)
        key_array.append(labels_line)
        labels.append(key_array)
    print_debug("So... all labels:")
    print_debug(labels) 
    return labels


def find_pulls(session, reposlug, base, state, repo=False, ok=False, fail=False):
    print_debug("")
    params_get=[["per_page","100"]]
    if base:
        params_get.append(["base",base])
        print_debug("Base: " + base)
    if state:
        params_get.append(["state",state])    
        print_debug("State: " + state)   
    #params_get.append(["sort","created"])  
    r = session.get('https://api.github.com/repos/' + reposlug + '/pulls', params=params_get)
    if not "200" in str(r.status_code):
        if fail:
            click.echo('{}'.format(repo) + " " + reposlug + " - " + fail)
            #continue
        else:
            ... # web
        return False
    if ok:
        click.echo('{}'.format(repo) + " " + reposlug + " - " + ok)
    else:
        ... # web
    pulls = []
    for i in range(len(r.json())):
        pulls.append(r.json()[i]['number']) # Founded PRs are stored in array pulls
    try: # multipage
        pages = int(r.links['last']['url'][::-1].split("=",maxsplit=1)[0])
        print_debug("Pages: " + str(pages))
        params_get.append(["page",0])
        for k in range(pages-1):
            params_get[-1][-1] = k+2
            r = session.get('https://api.github.com/repos/' + reposlug + '/pulls', params=params_get)
            for j in range(len(r.json())):
                pulls.append(r.json()[j]['number'])
    except KeyError: # obtained one page is enough    
        pass
    print_debug("Found PR:")
    for pull in pulls:
        print_debug(pull)
    return pulls


def find_pull_files(session, reposlug, pull):
    pull_error = False
    print_debug("")
    r = session.get('https://api.github.com/repos/' + reposlug + '/pulls/' + str(pull) + '/files', params=[["per_page","100"]])
    # check?
    pull_files = []
    for j in range(len(r.json())):
        pull_files.append(r.json()[j]['filename'])            
    try: # multipage
        #pages = int(r.links['last']['url'][-1])
        pages = int(r.links['last']['url'][::-1].split("=",maxsplit=1)[0])
        print_debug("Pages: " + str(pages))
        for k in range(pages-1):
            r = session.get('https://api.github.com/repos/' + reposlug + '/pulls/' + str(pull) + '/files', params=[["per_page","100"],["page",k+2]])
            for j in range(len(r.json())):
                pull_files.append(r.json()[j]['filename'])
    except KeyError: # obtained one page is enough    
        pass                        
    print_debug("Files of PR " + str(pull) + ":")
    print_debug(pull_files)
    return pull_files


def find_pull_labels(session, reposlug, pull, labels):
    r = session.get('https://api.github.com/repos/' + reposlug + '/issues/' + str(pull) + '/labels')
    pull_labels_i_raw = []
    for j in range(len(r.json())):
        pull_labels_i_raw.append(r.json()[j]['name'])
    print_debug("Current setting of labels of PR " + str(pull) + ":")
    print_debug(pull_labels_i_raw)
    # Filter only the labels known from configuration
    pull_labels_i = []
    seen = set()
    for key in range(len(labels)):
        for pull_label in pull_labels_i_raw:
            if labels[key][0] == pull_label:
                print_debug("  Label " + pull_label + " matches with labels in cofiguration.")
                if pull_label not in seen:
                    seen.add(pull_label)
                    pull_labels_i.append(pull_label)
    print_debug("Current setting of labels of PR " + str(pull) + " - filtered:")
    print_debug(pull_labels_i) 
    return pull_labels_i
    
def config_W():
    try:
        config_const = os.environ["FILABEL_CONFIG"]
    except KeyError:
        error_message = "Configuration not supplied in the shell constant variable $FILABEL_CONFIG!"
        return False, error_message
    config_const = config_const.split(":") # makes list of configuration files
    #for config_file in config_const:
    overall_parser = configparser.ConfigParser()
    try:
        #for config_file in config_const:
        overall_parser.read(config_const)
    except:
        error_message = "Configuration not usable -- not possible to read configuration file(s)!"
        return False, error_message 
    #overall_parser.sections()
    try:
        token = overall_parser['github']['token']
    except KeyError:
        error_message = "\n".join(["Auth configuration not usable!", str(overall_parser.sections()), str(config_const)])
        return False, error_message         
    if not "labels" in overall_parser:
        error_message = "\n".join(["Labels configuration not usable! ", str(overall_parser.sections()), str(config_const)])
        return False, error_message        
    return True, overall_parser        


def find_repos_W(overall_parser):
    overall_parser.sections()
    try:
        overall_parser['github']['repos']
    except:
        return False
    repos = []
    print_debug("Repos:")
    for repo in overall_parser['github']['repos'].splitlines():
        if repo:
            print_debug("    - Repo: " + repo)                
            repos.append(repo)
    print_debug("So... all repos:")
    print_debug(repos)   
    return repos
            

#Compare the HMAC hash signature
def verify_hmac_hash(data, signature):
    GitHub_secret = bytes('uplnemochroznetajneheslo', 'UTF-8')
    mac = hmac.new(GitHub_secret, msg=data, digestmod=hashlib.sha1)
    return hmac.compare_digest('sha1=' + mac.hexdigest(), signature)            
    
#def main_W():
    # Check if the shell constant variable $FILABEL_CONFIG is set
    #success, config_const = config_W()

@app.route('/',methods=['GET','POST'])
def index(reposlug=False, sdeleni=False):
    # Check if the shell constant variable $FILABEL_CONFIG is set and configuration is usable
    success, overall_parser = config_W()
    # Check if tokes is usable
    session = requests.Session()
    session.headers = {'User-Agent': 'Python'}
    def token_auth(req): # Why it is placed here?
        req.headers['Authorization'] = f'token {overall_parser["github"]["token"]}'
        return req
    session.auth = token_auth
    r = session.get('https://api.github.com/user')
    if not "200" in str(r.status_code): #200
        success = False
        overall_parser = "Auth configuration not usable!"

    username = r.json()['login']
    labels = find_labels(overall_parser)
    labels_rules = ""
    for labelset in labels:
         labels_rule = "File(s) with path(s) " + str(labelset[1])[1:-1] + " should have label " + labelset[0] + ". "
         labels_rules = "".join([labels_rules, labels_rule])
         
    if request.method == 'POST':
        #signature = request.headers.get('X-Hub-Signature')
        data = request.data
        #if verify_hmac_hash(data, signature):
        if True==True:
            if request.headers.get('X-GitHub-Event') == "ping":
                with open("file_ping.txt","w") as f:
                    f.write(str(request.data))
                return jsonify({'msg': 'Ok'})
            if request.headers.get('X-GitHub-Event') == "pull_request":
                with open("file_pull.txt","w") as f:
                    f.write(str(request.data))
                return jsonify({'msg': 'Ok'})
        else:
            abort(405)
            #test
    #success = False
    #overall_parser = str(dict(overall_parser.items('github')))
    
    
    
    
    #r = session.get('https://api.github.com/user/repos')
    
    # Find repos in configuration files
    #repos = find_repos_W(overall_parser)
    #if not repos:
    #    success = False
    #    overall_parser = "Any repository was not found in any configuration file(s)! Set the repositories in the file in the section [github], option repos = ..."    
    #repos_checked = str(repos)[1:-1]
    
    #for rep in repos:
    #    reposlug = "/".join([username,rep])
        # Find PRs in repository
    #    pulls = find_pulls(session, reposlug, False, False)
    #    sdeleni = str(pulls)
    #    if not pulls:
    #        results = "chyba"
    #        continue
    #    results = "ok"
        
    #sdeleni = str(r.json()[0]['name'])    
    
    if success:
        return render_template('filabel.html', username=username, labels_rules=labels_rules, sdeleni=sdeleni)
    else:
        return render_template('error.html', error_message=overall_parser)

def print_debug(text):
    #print(text)
    pass
    return    
    
if __name__ == '__main__':
    main()
