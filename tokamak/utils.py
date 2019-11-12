import subprocess
import sys
import re

def kill(pid):
    cmd = f"kill -9 {pid}"
    out = ""
    try:
        out = subprocess.check_call(cmd, shell=True).decode('utf-8')
    except subprocess.CalledProcessError as e:
        out = (
            "common::run_command() : [ERROR]: output = %s, error code = %s\n"
            % (e.output, e.returncode))
    finally:
        sys.stderr.write(out)
    return f"Exit code: {out}"


def pidofport(port, killall=False):
    cmd = f"fuser {port}/tcp"
    out = ""
    try:
        out = subprocess.check_output(cmd, shell=True).decode('utf-8')
    except subprocess.CalledProcessError as e:
        out = (
                "common::run_command() : [ERROR]: output = %s, error code = %s\n"
                % (e.output, e.returncode))
    finally:
        sys.stdout.write(out)
    pids = map(lambda x: int(x), re.findall(r'(\d+)', out)[1:])
    if killall:
        for pid in pids:
            kill(pid)