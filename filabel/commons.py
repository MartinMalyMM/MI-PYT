import requests
import fnmatch
import sys
import os
import json
import click
import configparser

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

def print_debug(text):
    #print(text)
    pass
    return  
