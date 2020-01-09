import subprocess
import os
import sys
import math
import os
import time
import subprocess
import sys

import subprocess

try:
    import matlab.engine
except Exception as e:
    print(f"{e.__class__.__name__} :: {e}")

def start_matlab_engine():
        err = None
        eng = None
        pid = None
        started = False
        try:
            import matlab.engine
        except ImportError as e:
            err = e
        if not err:
            active_pids = matlab.engine.find_matlab()
            if len(active_pids):
                pid = active_pids[-1]
                eng = matlab.engine.connect_matlab(pid)

            else:
                eng = matlab.engine.start_matlab()
                pid = os.getpid()
        started = eng is not None
        return eng, {"pid": pid, "ok": started, "err": err}
def get_matlab_bin():
    path_to_matlab = subprocess.check_output("which matlab", shell=True, encoding='utf-8').strip()
    if os.path.isfile(path_to_matlab):
        return path_to_matlab
    elif 'MATLAB_BIN' in os.environ and os.path.isfile(os.environ['MATLAB_BIN']):
        return os.environ['MATLAB_BIN']
    else:
        raise EnvironmentError(f"Path to matlab executable could not be resolved! You may need to explicitly set this path with the 'MATLAB_BIN' environment variable.")

def install_python_matlab_engine():
        err = None
        try:
            eng, status = start_matlab_engine()
            ok = status['ok'] and eng.eval("2+2") == 4
            import matlab.engine
            return ok, None

        except ImportError:
            print(f"Matlab engine not detected. Running installer...")
        except ModuleNotFoundError:
            print(f"Matlab engine not detected. Running installer...")
        except AssertionError:
            print(f"Matlab engine not working?")
        matlab_bin = get_matlab_bin()
        get_root_cmd = f"""{matlab_bin} -batch "fid = fopen('/tmp/out.txt', 'wt'); fprintf(fid, '%s', matlabroot); fclose(fid);" && echo $(head -n 1 /tmp/out.txt)"""
        root_dir = None
        try:
            root_dir = subprocess.check_output(get_root_cmd, shell=True, encoding="utf-8").strip()
        except Exception as e:
            err = RuntimeError(
                f"{e.__class__.__name__} :: Couldn't launch Matlab to extract the value of variable 'matlabroot'. \nError text: {e}\nShell command: {get_root_cmd}""")

        sub_dir = "extern/engines/python"
        if root_dir is None:
            for path, dirnames, filenames in os.walk("/"):
                if path.endswith(sub_dir):
                    root_dir = path[:len(sub_dir)*-1]
                    print(f"root dir is {root_dir}")
                    break

        filename = "setup.py"
        path_to_dir = os.path.join(root_dir, sub_dir)
        path_to_python_matlab_engine = os.path.join(path_to_dir, filename)
        path_to_curr_python_interpreter = sys.executable
        path = None
        eng = None
        pid = os.getpid()
        status = {}
        if not os.path.isdir(root_dir):
            err = FileNotFoundError(f"Error locating the matlab root directory! (Got: {root_dir})")
        elif not os.path.isfile(path_to_python_matlab_engine):
            err = FileNotFoundError(
                f"Error resolving the path to the matlab engine for python! Installer file {path_to_python_matlab_engine} does not exist.")
        else:
            os.chdir(path_to_dir)
            install_cmd = f"{path_to_curr_python_interpreter} setup.py install"
            proc = subprocess.run(install_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            if proc.returncode is not 0:
                err = RuntimeError(f"Error installing the python matlab bridge: {proc.stderr}")
            else:
                try:
                    eng, status = start_matlab_engine()
                    ok = status['ok'] and eng.eval("2+2") == 4
                    pid = status['pid']
                except Exception as e:
                    err = e.__class__(f"There was a problem loading the Matlab engine for python :: {e}")

        ok = err is None
        status.update({"ok": ok, "pid": pid, "err": err})

        return ok, err


def connect_matlab(session_id='foo'):
    ok, err = install_python_matlab_engine()
    try:
        eng = matlab.engine.connect_matlab(session_id)
    except matlab.engine.EngineError:
        cmd = subprocess.Popen(f'startmatlab --id="{session_id}"', shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        try:
            outs, errs = cmd.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        lockfile = f"/tmp/matlabsession_{session_id}"
        ok = False
        sleep_interval = 0.2
        max_wait = 20
        intervals = math.ceil(max_wait / sleep_interval)
        print(f"Waiting for MATLAB to generate lockfile...")
        for i in range(intervals):
            if not os.path.isfile(lockfile):
                time.sleep(0.2)
            else:
                print(f"Lockfile created.")
                with open(lockfile, 'r') as f:
                    ts = f.read()
                print(f"Session '{session_id}' initialized at {ts.strip()}")
                ok = True
                break

        if ok:
            can_connect = False
            for i in range(10):
                if session_id in matlab.engine.find_matlab():
                    print(f"Connecting to session '{session_id}'...")
                    can_connect = True
                    break
                else:
                    print(f"Waiting for session '{session_id}' to become available...")
                    time.sleep(1)
            if can_connect:
                eng = matlab.engine.connect_matlab(session_id)
            else:
                print(f"Matlab session '{session_id}' could not be loaded.")
                eng = None
        else:
            eng = None
    return eng

if __name__ == '__main__':
    ok, err = install_python_matlab_engine()
    print(f"Ok: {ok}")
    print(f"Err: {err}")
    import matlab.engine
    eng = connect_matlab('foobar')
    ans = eng.eval("3+8")
    print(f"3+8={ans}")