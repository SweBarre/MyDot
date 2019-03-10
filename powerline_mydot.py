from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import subprocess

from powerline.lib.unicode import out_u
from powerline.theme import requires_segment_info
from powerline.segments import Segment, with_docstring

@requires_segment_info
def status(pl, segment_info):
    command = "mydot status --silent"
    result = subprocess.run(command.split())
    if result.returncode:
        return [{'contents': 'MyDot', 'highlight_groups': ['exit_fail']}]
    else:
        return None