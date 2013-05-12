#!/usr/bin/env python

"""
To Do:
* Fix args and add useful ones
 * gitweb vs crucible, etc
 * html vs text
 * short vs long hash format
"""

import fileinput
import os
import re
import smtplib
import subprocess


def find_affected_files(diff_text):
    file_list = []
    for line in diff_text.split('\n'):
        if '--- a/' in line:
            file_list.append(line.split()[1][1:])
    return file_list


def prepend_repo_name(file_list):
    for x in range(0, len(file_list)):
        file_list[x] = str(commit['repo'] + file_list[x])
    return file_list


def find_common_string(s1, s2):
    count = 0
    try:
        while s1[count] == s2[count]:
            count += 1
    except IndexError:
        # occurs when we finish the shorter string
        # completely expected
        pass
    return s1[:count]


def trim_filename(s):
    for x in reversed(range(0, len(s))):
        if s[x] == '/':
            p = x
            break
    p += 1
    return s[0:p]


def find_common_path(file_list):
    if len(file_list) > 1:
        a = file_list[0]
        b = file_list[1]
        shared_path = find_common_string(a, b)
        if len(file_list) > 2:
            for x in range(2, len(file_list)):
                a = shared_path
                b = file_list[x]
                shared_path = find_common_string(a, b)
    elif len(file_list) == 1:
        shared_path = file_list[0]
    else:
        return ''

    return trim_filename(shared_path)


def transform_url(url, repo, hash):
    return url.replace('<repo>', repo).replace('<hash>', hash)


def git(command):
    args = ['git'] + command.split()
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    return p.stdout.read().strip()


def get_recipient():
    return git('config hooks.mailinglist')


def git_log(format_code, ref_name):
    return git(['log -n 1 --format=%s' % format_code, ref_name])


def get_repo_name():
    bare = git('rev-parse --is-bare-repository')
    if bare == 'true':
        name = os.path.basename(os.getcwd())
        if name.endswith('.git'):
            return name[:-4]
        return name
    else:
        return os.path.basename(os.path.dirname(os.getcwd()))


def send_email(message):
    sender = git('config hooks.envelopesender')
    recipients = get_recipient()
    try:
        s = smtplib.SMTP('localhost')
        s.sendmail(sender, recipients, message)
    except:
        exit(1)


def create_head_data(commit):

    result = re.match('^0*$', commit['old_hash'])

    if result:
        commit['action'] = 'create'
    else:
        result = re.match('^0*$', commit['new_hash'])
        if result:
            commit['action'] = 'delete'
        else:
            commit['action'] = 'update'

    if commit['action'] == 'create' or commit['action'] == 'update':
        commit['hash'] = commit['new_hash']
        commit['type'] = git('cat-file -t', commit['new_hash'])

    elif commit['action'] == 'delete':
        commit['hash'] = commit['old_hash']
        commit['type'] = git('cat-file -t', commit['old_hash'])

    else:
        exit(1)

    commit['branch'] = commit['ref_name'].split('/heads/')[1]
    url = 'https://crucible.example.com/changelog/<repo>?cs=<hash>'
    commit['url'] = transform_url(url,
                                  commit['repo'],
                                  commit['hash'])

    taglist = git('tag -l')
    commit['tag'] = 'none'
    if taglist:
        commit['tag'] = git('describe', commit['hash'], '--tags')

    commit['diff'] = ''
    if not result:
        commit['diff'] = git('diff %s..%s' % (commit['old_hash'],
                                              commit['new_hash']))

    commit['user'] = git_log('%cn', commit['ref_name'])
    commit['email'] = git_log('%ce', commit['ref_name'])
    commit['date'] = git_log('%ad', commit['ref_name'])
    commit['subject'] = git_log('%s', commit['ref_name'])
    commit['body'] = git_log('%b', commit['ref_name'])

    files = git('show --pretty=format: --name-only', commit['hash'])
    file_list = files.split('\n')
    files = ''
    for file in file_list:
        files += '%s/%s\n' % (commit['repo'], file)
    commit['files'] = files.strip()

    file_list = files.strip().split('\n')
    commit['shared_path'] = find_common_path(file_list)

    if commit['shared_path'] == str(commit['repo'] + '/'):

        try:
            file_list = find_affected_files(commit['diff'])
            file_list = prepend_repo_name(file_list, commit['repo'])
            commit['shared_path'] = find_common_path(file_list)

        except:
            commit['shared_path'] = str(commit['repo'] + '/')

    create_head_msg(commit)


def create_head_msg(commit):

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

New Hash:      %(new_hash)s
Old Hash:      %(old_hash)s
Shared Path:   %(shared_path)s

Files affected by this commit:
%(files)s

Crucible URL:      %(url)s

Diff:

%(diff)s
""" % commit

    message = header + body
    print message
    #send_email(message)


def create_tag_data(commit):

    commit['tag_name'] = commit['ref_name'].split('/tags/')[1]
    commit['old_hash_tag'] = git('describe --tags %s^' % commit['ref_name'])
    commit['points_to'] = git(
        'rev-parse --verify %s^{commit}' % commit['tag_name']
    )

    commit['user'] = git_log('%cn', commit['ref_name'])
    commit['email'] = git_log('%ce', commit['ref_name'])
    commit['date'] = git_log('%ad', commit['ref_name'])
    commit['subject'] = git_log('%s', commit['ref_name'])
    commit['body'] = git_log('%b', commit['ref_name'])

    url = 'https://crucible.example.com/changelog/<repo>?cs=<hash>'
    commit['url'] = transform_url(url,
                                  commit['repo'],
                                  commit['points_to'])
    create_tag_msg(commit)


def create_tag_msg(commit):

    header = """To: %(recipient)s
From: %(user)s <%(email)s>
Subject: git [%(repo)s] tag:%(tag_name)s created
""" % commit

    body = """
The following tag has been created:

Tag:        %(tag_name)s
Hash:       %(new_hash)s
Points To:  %(points_to)s
Replaces:   %(old_hash_tag)s

User:       %(user)s <%(email)s>
Date:       %(date)s

Comment:    %(subject)s

%(body)s

Crucible URL: %(url)s
""" % commit

    message = header + body
    print message
    #send_email(message)


def read_commit():
    """
    How to identify a merge commit?
    """

    # read stdin
    stdin = fileinput.input()[0].split()

    # read old_hash hash and new_hash hash (short versions)
    old_hash = stdin[0][:7]
    new_hash = stdin[1][:7]

    # determine action from hash
    if old_hash == '0000000':
        action = 'create'
    elif new_hash == '0000000':
        action = 'delete'
    else:
        action = 'update'

    # read ref name, type, value
    ref = stdin[2]
    ref_type, ref_value = ref.split('/')[1:]
    ref_type = ref_type[:-1]  # trim the s from the ref type

    # return the dict
    return {'old_hash': old_hash,
            'new_hash': new_hash,
            'action': action,
            'ref': ref,
            'ref_type': ref_type,
            'ref_value': ref_value,
            'repo': get_repo_name()}


def main():

    # get commit data from stdin
    commit = read_commit()

    # print old and new hashes
    # this should go in email bodies
    print '%s => %s' % (commit.get('old_hash', ''),
                        commit.get('new_hash', ''))

    # head commits
    if commit.get('ref_type', '') == 'head':
        subject = '[git] %s: branch %s %sd (%s)'
        subject = subject % (commit.get('repo', ''),
                             commit.get('ref_value', ''),
                             commit.get('action', ''),
                             '/')
        print 'H', subject
        #send_head_message()

    # tag commits
    elif commit.get('ref_type', '') == 'tag':
        subject = '[git] %s: tag %s %sd'
        subject = subject % (commit.get('repo', ''),
                             commit.get('ref_value', ''),
                             commit.get('action', ''))
        print 'T', subject
        #send_tag_message()


if __name__ == '__main__':
    main()
