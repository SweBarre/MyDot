from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import subprocess
from pathlib import Path

from powerline.lib.unicode import out_u
from powerline.theme import requires_segment_info
from powerline.segments import Segment, with_docstring

dotdir = "{}/{}".format(Path.home(), ".dotfiles")

@requires_segment_info
def status(pl, segment_info):
    os.chdir(dotdir)
    command = "git status --short"
    result = subprocess.run(command.split(), stdout=subprocess.PIPE)
    if result.returncode:
        return [{'contents': 'MyDot:error', 'highlight_groups': ['exit_fail']}]
    else:
        if result.stdout:
            return [{'contents': 'MyDot', 'highlight_groups': ['exit_fail']}]
        command = "git cherry -v origin/master"
        result = subprocess.run(command.split(), stdout=subprocess.PIPE)
        if result.returncode:
            return [{'contents': 'MyDot:error', 'highlight_groups': ['exit_fail']}]
        elif result.stdout:
            return [{'contents': 'MyDot', 'highlight_groups': ['exit_success']}]
        return None
