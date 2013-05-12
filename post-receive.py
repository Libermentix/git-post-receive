#!/usr/bin/env python

"""
To Do:
* Fix all the bad algorithms in the convenience functions section
* Fix path algorithm
 * common_string function is decent
 * could approach the problem from the list perspective
 * i.e. focus on infinite size set instead of one string to one string
* Fix file find algorithm
 * git diff --name-status > parsing diff text
 * there's probably something better still
* Fix args and add useful ones
 * gitweb vs crucible, etc
 * html vs text
 * short vs long hash format
 * email reply-to field somehow
"""

import fileinput
import os
import re
import smtplib
import subprocess


"""
Convenience functions
"""
def find_common_string(s1, s2):
    count = 0
    try:
        while s1[count] == s2[count]:
            count += 1
    except IndexError:
        # occurs when we finish the shorter string
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


#def git_log(format_code, ref_name):
#    return git('log -n 1 --format=%s %s' % (format_code, ref_name))


def get_commit_info(format_code, commit_id):
    return git('diff-tree -s --format=%s %s' % (format_code,
                                                commit_id))


def get_repo_name():
    bare = git('rev-parse --is-bare-repository')
    if bare == 'true':
        name = os.path.basename(os.getcwd())
        if name.endswith('.git'):
            return name[:-4]
        return name
    else:
        return os.path.basename(os.path.dirname(os.getcwd()))

"""
Work functions
"""
def send_email(message):
    sender = git('config hooks.envelopesender')
    recipients = git('config hooks.mailinglist')
    try:
        s = smtplib.SMTP('localhost')
        s.sendmail(sender, recipients, message)
    except:
        exit(1)


def create_tag_data(commit):
    old_hash_tag = git('describe --tags %s^' % commit.get('ref'))
    points_to = git('rev-parse --verify %s^{commit}' % commit.get('ref_val'))


def read_commit():
    """
    Reads and generates data about a commit, and then returns a dictionary
    representation of that commit data.

    @return: dictionary containing commit data
    """

    # read hashes and ref name
    stdin = fileinput.input()[0].split()
    old_hash = stdin[0][:7]
    new_hash = stdin[1][:7]
    ref = stdin[2]
    ref_val = ref.split('/')[2]

    # determine action from hash
    if old_hash == '0000000':
        action = 'create'
    else:
        if new_hash == '0000000':
            action = 'delete'
        else:
            action = 'update'

    # get repository name
    repo = get_repo_name()

    return {'old_hash': old_hash,
            'new_hash': new_hash,
            'ref': ref,
            'ref_val': ref_val,
            'action': action,
            'repo': repo}


def process_head(commit):
    """
    To Do:
    * Figure out what data should go in create/delete message bodies
    """

    # build subject line
    subject = '%s: branch %s %sd'
    subject = subject % (commit.get('repo', 'unknown repo'),
                         commit.get('ref_val', 'unknown branch'),
                         commit.get('action', 'change'))

    if commit.get('action' , '') == 'update':

        # determine affected files and their shared path
        new_hash = commit.get('new_hash', None)
        if new_hash is not None:
            list_files = 'diff-tree --no-commit-id --name-only -r %s' % new_hash
            file_list = git(list_files).split('\n')
            if len(file_list) == 1:
                path = '%s/%s' % (commit.get('repo', 'unknown repo'),
                                  file_list[0])
            elif len(file_list) > 1:
                path = '%s/%s' % (commit.get('repo', 'unknown repo'),
                                  find_common_path(file_list))
            else:
                path = ''
        else:
            path = ''

        # add path to subject
        subject += ' (%s)' % path

        # get commit info
        author_name = get_commit_info('%an', new_hash)
        author_email = get_commit_info('%ae', new_hash)
        commit_date = get_commit_info('%cd', new_hash)
        commit_message = get_commit_info('%s', new_hash)
        commit_body = get_commit_info('%b', new_hash)
        commit_diff = git('diff %s..%s' % (commit.get('old_hash', ''),
                                           commit.get('new_hash', '')))

        # build message body
        body = 'Author: %s <%s>' % (author_name, author_email)
        body += '\nDate: %s' % commit_date
        body += '\nSubject: %s' % commit_message
        if commit_body != '':
            body += '\nBody:\n%s' % commit_body
        body += '\n\nFiles affected by this commit:'
        for file_name in file_list:
            body += '\n%s' % file_name
        body += '\n\nCode review URL:'
        body += '\nhttp://lol'
    else:
        body = None
        commit_diff = None

    print 'S', subject
    print 'B', body
    exit(0)

    # return subject, body, and diff text
    return subject, body, commit_diff


def process_tag(commit):
    """
    Normal? Annotated? Signed?
    Author, E-Mail, Date for the tag vs. for the commit
    """

    # generate subject line
    subject = '%s: tag %s %sd'
    subject = subject % (repo,
                         commit.get('ref_val', ''),
                         action)

    # generate message body
    if action == 'create':
        body = '%s tag %s points to %s.'
        body = body % (repo,
                       commit.get('ref_val', ''),
                       commit.get('new_hash', ''))

        # git log stores commits, not tags
        # note: the values for tagger, email, and date actually point to
        #       the commit referenced by the tag (instead of the tag)
        # use git for-each-ref for this (?)
        # note: you can only pull tag info (tagger, date, etc.) from an
        #       annotated tag.
        """
        git for-each-ref --count=3 --sort='-*authordate' \
        --format='From: %(*authorname) %(*authoremail)
        Subject: %(*subject)
        Date: %(*authordate)
        Ref: %(*refname)

        %(*body)
        ' 'refs/tags'
        """
        #tagger = git_log('%cn', commit.get('ref', ''))
        #email = git_log('%ce', commit.get('ref', ''))
        #date = git_log('%cd', commit.get('ref', ''))
        #body += '\n\nTagger: %s <%s>\n' % (tagger, email)
        #body += 'Date: %s\n' % date

    elif action == 'delete':
        body = '%s tag %s deleted.'
        body = body % (repo,
                       commit.get('ref_val', ''))

    else:
        body = ''


def main():

    # get commit data from stdin
    commit = read_commit()

    # head commits
    if 'head' in commit.get('ref', ''):
        subject, body, diff = process_head(commit)
        #send_email(subject, body, diff)

    # tag commits
    if 'tag' in commit.get('ref', ''):
        subject, body = process_tag(commit)
        #send_email(subject, body)

if __name__ == '__main__':
    main()
