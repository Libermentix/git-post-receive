#!/usr/bin/env python

"""
Copyright (c) 2013, Will Roberts <wroberts@jawbone.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the organization ("Jawbone") nor the names of its
      contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL COPYRIGHT HOLDER BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import config # try to axe this soon
from fileinput import input
import logging
import os
from re import match
from smtplib import SMTP
from subprocess import Popen, PIPE

def createLogger(target_file):
    logger = logging.getLogger(__name__)
    logger.handlers = []
    logger.addHandler(logging.FileHandler(target_file))
    return logger

def findAffectedFiles(diff_text):
    file_list = []
    for line in diff_text.split('\n'):
        if '--- a/' in line:
            file_list.append(line.split()[1][1:])
    return file_list

def prependRepoName(file_list):
    for x in range(0, len(file_list)):
        file_list[x] = str(commit['repo'] + file_list[x])
    return file_list

def findCommonString(a,b):
    if len(a) < len(b):
        limit = len(a)
    else:
        limit = len(b)
    c = ''
    for x in range(0,limit):
        if a[x] == b[x]:
            c = c + a[x]
        else:
            break
    return c

def trimFilename(s):
    for x in reversed(range(0,len(s))):
        if s[x] == '/':
            p = x
            break
    p += 1
    return s[0:p]

def findCommonPath(file_list):
    if len(file_list) > 1:
        a = file_list[0]
        b = file_list[1]
        shared_path = findCommonString(a,b)
        if len(file_list) > 2:
            for x in range(2,len(file_list)):
                a = shared_path
                b = file_list[x]
                shared_path = findCommonString(a,b)
    elif len(file_list) == 1:
        shared_path = file_list[0]
    else:
        return ''

    return trimFilename(shared_path)

def transformUrl(url, repo, hash):
    url = url.replace('<repo>', repo)
    url = url.replace('<hash>', hash)
    return url

def git(args):
    args = ['git'] + args
    p = Popen(args, stdout = PIPE)
    return p.stdout.read().strip()

def getRecipientAddress():
    recipients = git(['config', 'hooks.mailinglist'])
    return recipients

def gitLog(format_code, ref_name):
    return git(['log', '-n', '1', '--format=%s' % format_code, ref_name])

def getRepoName():
    bare = git(['rev-parse', '--is-bare-repository'])
    if bare == 'true':
        name = os.path.basename(os.getcwd())
        if name.endswith('.git'):
            name = name[:-4]
        return name
    else:
        return os.path.basename(os.path.dirname(os.getcwd()))

def sendEmail(message):
    sender = config.sender
    recipients = getRecipientAddress()
    try:
        s = SMTP('localhost')
        s.sendmail(sender, recipients, message)
    except:
        log.exception('The sendEmail() function encountered an error.')
        exit(1)

def createHeadData(commit):
    
    result = match('^0*$', commit['old'])

    if result:
        commit['action'] = 'create'
    else:
        result = match('^0*$', commit['new'])
        if result:
            commit['action'] = 'delete'
        else:
            commit['action'] = 'update'

    if commit['action'] == 'create' or commit['action'] == 'update':
        commit['hash'] = commit['new']
        commit['type'] = git(['cat-file', '-t', commit['new']])

    elif commit['action'] == 'delete':
        commit['hash'] = commit['old']
        commit['type'] = git(['cat-file', '-t', commit['old']])

    else:
        exit(1)

    commit['branch'] = commit['ref_name'].split('/heads/')[1]
    commit['url'] = transformUrl(commit['url'], commit['repo'], commit['hash'])

    taglist = git(['tag', '-l'])
    commit['tag'] = 'none'
    if taglist:
        commit['tag'] = git(['describe', commit['hash'], '--tags'])

    commit['diff'] = ''
    if not result:
        commit['diff'] = git(['diff', '%s..%s' % (commit['old'], commit['new'])])

    commit['user'] = gitLog('%cn', commit['ref_name'])
    commit['email'] = gitLog('%ce', commit['ref_name'])
    commit['date'] = gitLog('%ad', commit['ref_name'])
    commit['subject'] = gitLog('%s', commit['ref_name'])
    commit['body'] = gitLog('%b', commit['ref_name'])

    file_list = git(['show', '--pretty=format:', '--name-only', commit['hash']]).split('\n')
    files = ''
    for file in file_list:
        files += '%s/%s\n' % (commit['repo'], file)
    commit['files'] = files.strip()

    file_list = files.strip().split('\n')
    commit['shared_path'] = findCommonPath(file_list)

    if commit['shared_path'] == str(commit['repo'] + '/'):

        try:
            file_list = findAffectedFiles(commit['diff'])
            file_list = prependRepoName(file_list, commit['repo'])
            commit['shared_path'] = findCommonPath(file_list)

        except:
            commit['shared_path'] = str(commit['repo'] + '/')

    createHeadMessage(commit)

def createHeadMessage(commit):

    header = """To: %(recipient)s
From: %(user)s <%(email)s>
Subject: git [%(repo)s] branch:%(branch)s path:%(shared_path)s...
""" % commit

    body = """
Repository:    %(repo)s
Branch:        %(branch)s
Tag:           %(tag)s
Committer:     %(user)s <%(email)s>
Commit Date:   %(date)s

Comment:       "%(subject)s"

%(body)s

New Hash:      %(new)s
Old Hash:      %(old)s
Shared Path:   %(shared_path)s

Files affected by this commit:
%(files)s

Crucible URL:      %(url)s

Diff:

%(diff)s
""" % commit

    message = header + body
    sendEmail(message)

def createTagData(commit):

    commit['tag_name'] = commit['ref_name'].split('/tags/')[1]
    commit['old_tag'] = git(['describe', '--tags', '%s^' % commit['ref_name']])
    commit['points_to'] = git(['rev-parse', '--verify', '%s^{commit}' % commit['tag_name']])

    commit['user'] = gitLog('%cn', commit['ref_name'])
    commit['email'] = gitLog('%ce', commit['ref_name'])
    commit['date'] = gitLog('%ad', commit['ref_name'])
    commit['subject'] = gitLog('%s', commit['ref_name'])
    commit['body'] = gitLog('%b', commit['ref_name'])

    commit['url'] = transformUrl(commit['url'], commit['repo'], commit['points_to'])
    createTagMessage(commit)

def createTagMessage(commit):

    header = """To: %(recipient)s
From: %(user)s <%(email)s>
Subject: git [%(repo)s] tag:%(tag_name)s created
""" % commit

    body = """
The following tag has been created:

Tag:        %(tag_name)s
Hash:       %(new)s
Points To:  %(points_to)s
Replaces:   %(old_tag)s

User:       %(user)s <%(email)s>
Date:       %(date)s

Comment:    %(subject)s

%(body)s

Crucible URL: %(url)s
""" % commit

    message = header + body
    sendEmail(message)

def main():

    commit = {}

    stdin = input()[0].split()
    commit['old'] = stdin[0]
    commit['new'] = stdin[1]
    commit['ref_name'] = stdin[2]

    commit['url'] = 'https://crucible.example.com/changelog/<repo>?cs=<hash>'
    commit['repo'] = getRepoName()
    commit['recipient'] = getRecipientAddress()

    if 'heads' in commit['ref_name']:
        createHeadData(commit)
    elif 'tags' in commit['ref_name']:
        createTagData(commit)
    else:
        log.debug('Neither "heads" nor "tags" was in this ref name: %s' % ref_name)

if __name__ == '__main__':

    log = createLogger('/var/log/git-updates.log')

    try:
        main()
    except:
        log.exception('Encountered an exception in the main loop.')
