#!/usr/bin/env python3
import hmac
import hashlib
from flask import Flask, request, jsonify, abort, render_template
from .commons import *

def create_app(var):
    app = Flask(__name__)

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
            signature = request.headers.get('X-Hub-Signature')
            secret = overall_parser["github"]["secret"]
            if verify_hmac_hash(request.data, signature, secret):
            #if True==True:
                if request.headers.get('X-GitHub-Event') == "ping":
                    return jsonify({'msg': 'Ok'})
                if request.headers.get('X-GitHub-Event') == "pull_request":
                    #data = json.loads(request.data)
                    data = request.data.decode('utf-8')
                    data = json.loads(data)
                    reposlug = str(data['repository']['full_name'])
                    
                    # Find PRs in repository
                    pulls = find_pulls(session, reposlug, base=False, state="open")
                    if pulls:
                        for pull in pulls:
                            pull_error = False
                            #
                            # Sorry, it would be better to write it nicely
                            # and put next lines to a function. I have tried
                            # it but I did not manage repair bugs...
                            #
                            
                            delete_old = True
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
                                    #click.echo('{}'.format(pr) + " https://github.com/" + reposlug + "/" + str(pull) + " - " + fail)
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
                                    #click.echo('{}'.format(pr) + " https://github.com/" + reposlug + "/pull/" + str(pull) + " - " + fail)
                                    continue 
                    return jsonify({'msg': 'Ok'})
            else:
                abort(405)
        if success:
            return render_template('filabel.html', username=username, labels_rules=labels_rules, sdeleni=sdeleni)
        else:
            return render_template('filabel.html', username="---", labels_rules="---", sdeleni=overall_parser)
    
    
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
        try:
            token = overall_parser['github']['token']
        except KeyError:
            error_message = "\n".join(["Auth configuration not usable!", str(overall_parser.sections()), str(config_const)])
        try:
            secret = overall_parser['github']['secret']
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
    def verify_hmac_hash(data, signature, secret, encoding='utf-8'):        
        h = hmac.new(secret.encode(encoding), data, hashlib.sha1)
        return hmac.compare_digest('sha1=' + h.hexdigest(), signature) 
    
    return app

