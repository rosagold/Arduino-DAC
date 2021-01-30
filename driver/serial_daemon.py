import daemon
import daemon.pidfile
import os
import click
import time
import signal

_PIDFILE = '/home/rg/sandbox/daemon.pid'


def main():
    f = "daemon_file"

    pid = os.getpid()
    while True:

        if not os.path.exists(f):
            with open(f, mode='w') as file_:
                file_.write(f"pid={pid}\n")

        time.sleep(1)


def _start():
    context = daemon.DaemonContext(
        pidfile=daemon.pidfile.PIDLockFile(_PIDFILE),
        working_directory='/home/rg/sandbox/',
    )

    with context:
        main()


def get_pid():
    with open(_PIDFILE, 'r') as fd:
        return int(fd.readline())


def _stop_or_kill(kill=False):
    try:
        pid = get_pid()

    except FileNotFoundError:
        raise RuntimeError("The daemon seems not to exist. Was it started already?")

    except ValueError:
        msg = "The daemon's lock-file seems corrupted."
        try:
            os.remove(_PIDFILE)
        except Exception:
            raise RuntimeError(msg + f"Could not remove it. Try to start the daemon anew. If this fails, "
                                     f"remove the lock file manually: '{_PIDFILE}' ")

        raise RuntimeError(msg + "we removed it.")

    action = "killing" if kill else "stopping"
    print(f"{action} daemon with PID={pid}")

    try:

        os.kill(pid, signal.SIGTERM)
        if kill:
            os.kill(pid, signal.SIGKILL)

    except ProcessLookupError:
        pass

    return


@click.command()
@click.option('--start', is_flag=True, help="start the daemon. If already running do nothing.")
@click.option('--stop', is_flag=True, help="stop the daemon gracefully (SIGTERM). If not running, do nothing.")
@click.option('--kill', is_flag=True, help="force stop of daemon (SIGKILL). If not running, do nothing.")
def evaluate_args(start, stop, kill):
    if start and (stop or kill):
        raise ValueError("Cannot start and stop/kill at the same time.")

    if stop or kill:
        _stop_or_kill(kill)
        return

    if os.path.exists(_PIDFILE):
        try:
            pid = get_pid()
        except (FileNotFoundError, ValueError):
            print("starting daemon")
        else:
            print(f"daemon seems already running under PID={pid}")
    _start()


if __name__ == '__main__':
    evaluate_args()
