git-post-receive
================
A modular python plugin for git's post-receive hook.

How the post-receive hook works
===============================
When a user pushes code into a git repository, git runs through a series of
event hooks which can call scripts when triggered. One of these is the
'post-receive' hook, which is triggered after a commit/push. A
'post-receive' script is located in the 'hooks' directory of your git
repository (on the server hosting the repository) by default:

    <git repository>/hooks/post-receive

When this script is called, git passes three things to STDIN:

    <hash for old revision> <hash for new revision> <ref name>

We pass these values to post-receive-email.py to format our e-mail messages.

Installation
============
In order to use this script, you'll need to modify your post-receive script
to send data to this script. You might use a shell script to do this:

    # post-receive
    > #!/bin/sh
    > read stdin
    > echo $stdin | /usr/bin/env python post-receive-email.py

If you already have existing post-receive scripts in place, simply add those
scripts to your post-receive file as well:

    # post-receive
    > #!/bin/sh
    > read stdin
    > echo $stdin | existing-script.sh
    > echo $stdin | /usr/bin/env python post-receive-email.py

Configuration
=============
Provided with this script is a file called 'config.py'. Modify config.py 
for your environment, and post-receive-email.py will pick up the changes 
automatically when it is run. Both files must be in the same directory 
in your filesystem.


    # Sender
    # This variable determines the mailbox from which messages are sent.
    # The 'From:' field in e-mails will be populated with the user who
    # made the commit for that particular e-mail.
    sender = 'user@example.com'

    # Recipients
    # This list contains e-mail addresses to send git notifications to.
    # You can include any number of addresses here, as long as each 
    # address is enclosed by single quotes and is separated by a comma.
    recipients = ['user@example.com', 'user@example.com']

    # HTML
    # Specify whether or not to send messages in HTML format. The default
    # is False. Set to True to enable HTML messages.
    html = False

    # URL
    # Specify a URL format to use for viewing diffs. The default URL format
    # is for Atlassian Crucible or Fisheye, but you can specify other URL
    # formats as well. This option reads for two special keywords: <repo>
    # and <hash>, and uses these placeholders to generate a valid URL for
    # your code viewer. For example, you might provide a url format like
    # this:
    #
    # 'http://code.example.com/<repo>/view?hash=<hash>'
    #
    # This script will generate a valid URL by subsituting the repo and
    # hash of the current commit, and this URL will be added to the body of
    # e-mail notifications.
    url = 'https://crucible.example.com/changelog/<repo>?cs=<hash>'

You can now also use a local configuration to specify recipients. This is
useful when you have multiple repositories using the same post-receive-email.py
script. To do this, create a file called 'local_config.py' in the hooks directory
for your repository which contains the following:

    #!/usr/bin/python
    recipients = ['recipient1@example.com', 'recipient2@example.com', '...']

License
=======

    Copyright (c) 2012, Will Roberts <wroberts@jawbone.com>
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
