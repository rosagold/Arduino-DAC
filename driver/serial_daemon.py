import sys
import daemon
from daemon.pidfile import PIDLockFile
import os
import click
import time
import signal
import logging
from multiprocessing import Process

_WORKING_DIR = '/home/rg/sandbox/'
_PID_FILE = _WORKING_DIR + 'daemon.pid'
_LOG_FILE = _WORKING_DIR + 'daemon.log'
_ERR_FILE = _WORKING_DIR + 'daemon.err'

_LOG_LEVEL = logging.DEBUG


def daemon_code():
    """
    This should not spawn Subprocesses unless this are multiprocessing.daemons.
    ``p = Process(target=my_func, daemon=True)``. Those are not the same daemons
    as which this process will run ! If a real new process is started here, the
    script cannot end this daemon properly until the subprocess is ended. Only
    option is to kill and even then the subprocess will survive.

    Returns
    -------
    never: NoReturn
        The function should never return, unless the daemon just live for a very
        specific purpose, which is fulfilled with its end. Otherwise a infinite
        loop should be entered.
    """
    import serial_driver_as_class as sd
    drv = sd.SerialDriver(force=True)
    drv.run()  # no return


def _get_pid_from_pidfile():
    with open(_PID_FILE, 'r') as fd:
        return int(fd.readline())


def get_daemon_pid():
    """
    Get the PID of the daemon.

    Returns
    -------
    pid: int or None
        PID of the daemon if it is running, None otherwise.
    """
    try:
        return _get_pid_from_pidfile()
    except (FileNotFoundError, ValueError):
        return None


def start_daemon():
    """

    Returns
    -------
    pid: int or None
        PID of the daemon if started successfully, None otherwise.

    """
    pid = get_daemon_pid()

    if pid is None:
        print("starting daemon")
    else:
        print(f"daemon seems already running under PID={pid}")

    log_fd = open(_LOG_FILE, 'w+')
    context = daemon.DaemonContext(
        pidfile=PIDLockFile(_PID_FILE),
        working_directory=_WORKING_DIR,
        stdout=log_fd,
        stderr=log_fd,
    )

    def start():

        with context:
            logger = logging.getLogger('serial_driver_daemon')
            logger.setLevel(logging.DEBUG)
            fh = logging.FileHandler(_ERR_FILE, mode='w+')
            fh.setLevel(_LOG_LEVEL)
            logger.addHandler(fh)

            try:
                daemon_code()
            except Exception:
                logger.exception("daemon failed")
                raise

    # daemonize the current(!) process,
    # but we don't want to be it, because
    # we could not run more code then..
    p = Process(target=start, name="some_foo")
    p.start()
    p.join(1)

    if p.is_alive() or p.exitcode != 0:
        raise RuntimeError("something went wrong")

    # wait until file was created and just
    # a bit longer until it also was written
    t0 = time.time()
    while time.time() - t0 < 5:
        if os.path.exists(_PID_FILE):
            break
    time.sleep(0.1)

    return get_daemon_pid()


def stop_daemon(kill=False):
    try:
        pid = _get_pid_from_pidfile()

    except FileNotFoundError:
        raise RuntimeError("The daemon seems not to exist. Was it started already?")

    except ValueError:
        msg = "The daemon's lock-file seems corrupted."
        try:
            os.remove(_PID_FILE)
        except Exception:
            raise RuntimeError(msg + f"Could not remove it. Try to start the daemon anew. If this fails, "
                                     f"remove the lock file manually: '{_PID_FILE}' ")

        raise RuntimeError(msg + "we removed it.")

    action = "killing" if kill else "stopping"
    print(f"{action} daemon with PID={pid}")

    try:
        os.kill(pid, signal.SIGTERM)

        if kill:

            try:
                time.sleep(0.1)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    finally:

        try:
            os.remove(_PID_FILE)
        except FileNotFoundError:
            pass

    return


@click.command()
@click.option('--start', is_flag=True, help="start the daemon. If already running do nothing.")
@click.option('--stop', is_flag=True, help="stop the daemon gracefully (SIGTERM). If not running, do nothing.")
@click.option('--restart', is_flag=True, help="restart the daemon. If not running, just start it.")
@click.option('--kill', is_flag=True, help="force stop of daemon (SIGKILL). If not running, do nothing.")
def _evaluate_args(start, stop, restart, kill):
    if start and (stop or kill):
        raise ValueError("Cannot start and stop/kill at the same time.")

    if stop or kill:
        stop_daemon(kill)

    if restart:
        try:
            stop_daemon(kill)
        except (RuntimeError, ProcessLookupError):
            pass

    if restart or start:
        pid = start_daemon()
        print(f"PID: {pid}")

    if start or stop or restart or kill:
        return

    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()


if __name__ == '__main__':
    _evaluate_args()
