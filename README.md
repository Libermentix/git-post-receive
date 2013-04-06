git-post-receive
================
A modular Python plugin for git's post-receive hook.

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

We pass these values to post-receive.py to format our e-mail messages.

Installation
============
In order to use this script, you'll need to modify your post-receive script
to send data to this script. You might use a shell script to do this:

    # post-receive
    > #!/bin/sh
    > read stdin
    > echo $stdin | /usr/bin/env python post-receive.py

If you already have existing post-receive scripts in place, simply add those
scripts to your post-receive file as well:

    # post-receive
    > #!/bin/sh
    > read stdin
    > echo $stdin | existing-script.sh
    > echo $stdin | /usr/bin/env python post-receive.py

Configuration
=============
To use this script, you'll need to configure your git configuration for your
repo. Below is an example of a `.git/config` file:


    [hooks]
        mailinglist = to@example.com
        emailprefix = "[git] "
        envelopesender = "from@example.com"

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
