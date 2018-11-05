#!/usr/bin/env python3
import click
import configparser
from .commons import *

  
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
