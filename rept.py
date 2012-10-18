#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import os
import subprocess
import configparser
import xml.etree.ElementTree as ElementTree

CONFIG_FILE = "config.rept"

COMMANDS = {
    "clone": lambda baseDir: processRepos(baseDir, 'clone', lambda repository: not os.path.exists(os.path.join(baseDir, repository['dst']))),
    "fetch": lambda baseDir: processRepos(baseDir, 'fetch', lambda repository: True),
    "update": lambda baseDir: processRepos(baseDir, 'update', lambda repository: True),
    "scan": lambda baseDir: scan(baseDir)
}

def extractUrl(directory, fileName, section, option):
    configFile = os.path.join(directory, fileName)
    if os.path.isfile(configFile):
        config = configparser.RawConfigParser()
        config.read([configFile])
        if config.has_section(section):
            return config.get(section, option)
    return None

def extractUrlSvn(directory):
    try:
        svnInfoString = subprocess.check_output("cd {} && svn info --xml 2> /dev/null".format(directory), shell=True)
        svnInfoElement = ElementTree.fromstring(svnInfoString.decode('utf-8'))
        return svnInfoElement.find("entry/url").text
    except:
        return None

DEFAULT_REPOS_CONFIG = {
    "git": {
        "url": (extractUrl, ('.git/config', 'remote "origin"', 'url')),
        "commands": {
            "git-clone": "git clone $src $dst",
            "git-fetch": "cd $dst && git fetch",
            "git-pull": "cd $dst && git pull",
            "git-pull-rebase": "cd $dst && git pull --rebase",
        },
        "default": {
            "clone": "git-clone",
            "fetch": "git-fetch",
            "update": "git-pull"
        }
    },
    "hg": {
        "url": (extractUrl, ('.hg/hgrc', 'paths', 'default')),
        "commands": {
            "hg-clone": "hg clone $src $dst",
            "hg-pull": "cd $dst && hg pull",
            "hg-pull-update": "cd $dst && hg pull -u"
        },
        "default": {
            "clone": "hg-clone",
            "fetch": "hg-pull",
            "update": "hg-pull-update"
        }
    },
    "svn": {
        "url": (extractUrlSvn, ()),
        "commands": {
            "svn-checkout": "svn checkout $src $dst",
            "svn-update": "cd $dst && svn update"
        },
        "default": {
            "clone": "svn-checkout",
            "update": "svn-update"
        }
    }
}

def readConfig(baseDir):
    with open(os.path.join(baseDir, CONFIG_FILE), 'r') as configFile:
        configTree = json.load(configFile)
        return configTree

def runCommand(baseDir, repository, command):
    command = command.replace('$src', repository['src']) 
    command = command.replace('$dst', os.path.join(baseDir, repository['dst'])) 
    command = "cd {} && ".format(baseDir) + command
    subprocess.call(command, shell=True)

def processRepos(baseDir, commandName, filterFunc):
    configTree = readConfig(baseDir)
    print("Found {} repositories in configuration file.".format(len(configTree['repositories'])))
    for repository in configTree['repositories']:
        if filterFunc(repository) and commandName in repository:
            print("Running '{}' inside '{}' repository.".format(commandName, repository['dst']))
            runCommand(baseDir, repository, configTree['commands'][repository[commandName]])
        else:
            print("Skipping '{}' repository.".format(repository['dst']))

def scanRepository(directory):
    for repositoryName, repositoryConfig in DEFAULT_REPOS_CONFIG.items():
        urlFunc, params = repositoryConfig['url']
        url = urlFunc(directory, *params)
        if url is not None:
            return repositoryName, url
    return None

def addRepository(config, repositoryName, src, dst):
    repositoryEntry = {
        "src": src,
        "dst": dst
    }
    defaultCommands = DEFAULT_REPOS_CONFIG[repositoryName]['default']
    for command in COMMANDS:
        if command in defaultCommands:
            repositoryEntry[command] = defaultCommands[command]
    config['repositories'].append(repositoryEntry)

def scan(baseDir):
    config = {
        'commands': {},
        'repositories': []
    }
    for repositoryName, repositoryConfig in DEFAULT_REPOS_CONFIG.items():
        config['commands'].update(repositoryConfig['commands'])
    for entry in sorted(os.listdir(baseDir)):
        directory = os.path.join(baseDir, entry)
        if os.path.isdir(directory):
            repository = scanRepository(directory)
            if repository is not None:
                repositoryName, repositoryUrl = repository
                print("Found '{}' repository in '{}'.".format(repositoryName, entry))
                addRepository(config, repositoryName, repositoryUrl, entry)
            else:
                print("Skipping '{}' - not a known repository.".format(entry))
    with open(os.path.join(baseDir, CONFIG_FILE), 'w') as configFile:
        json.dump(config, configFile, indent=4)
        print("Saved configuration to '{}'".format(CONFIG_FILE))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage multiple repositories with single command.")
    parser.add_argument('command', choices=COMMANDS.keys(), help="Command to execute")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help="Base directory (current directory is default)")
    args = parser.parse_args()
    COMMANDS[args.command](args.directory)
