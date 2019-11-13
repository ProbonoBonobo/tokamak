#!/usr/local/bin/env python
from gemeinsprache.utils import run_shell_command

class ExecutableShellCommand:
    def __init__(self, cmd):
        self.input = cmd
        self.ok, self.output, self.exit_code , self.error_msg = run_shell_command(cmd)
