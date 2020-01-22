import sys
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from tokamak.utils import killprog, killport
import subprocess
port = 8050
def run_server():
    killport(port)
    try:
        import fcntl
        import os
        import sys
        # make stdin a non-blocking file
        fd = sys.stdin.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        proc = subprocess.run(f"gunicorn demo:server -b localhost:{port} --workers 4 --worker-class gevent --timeout 180", shell=True, stdout=fd, stderr=fd)
    except KeyboardInterrupt:
        print(f"Terminating server...")
        pass
    except Exception as e:
        print(e.__class__.__name__ + " :: " + str(e))
    return

class MyHandler(PatternMatchingEventHandler):
    patterns = ["*.py", "*.pyc"]
    def __init__(self):
        super().__init__()
        run_server()


    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        print(event.src_path, event.event_type)  # print now only for degug
        try:
            killprog("matlab")
            run_server()
        except KeyboardInterrupt:
            print(f"Interrupted!")


    def on_modified(self, event):
        self.process(event)


    def on_created(self, event):
        self.process(event)
        killprog("matlab")
        run_server()
if __name__ == '__main__':
    if __name__ == '__main__':
        args = sys.argv[1:]
        observer = Observer()
        observer.schedule(MyHandler(), path=args[0] if args else '.', recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        observer.join()
