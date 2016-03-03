"""
Partial backport of Python 3.5's test.support code.

This should contain everything needed to run test_weakref.

Backport modifications are marked with marked with "XXX backport".
"""
import collections
import os
import re
import subprocess
import sys


def strip_python_stderr(stderr):
    """Strip the stderr of a Python process from potential debug output
    emitted by the interpreter.
    This will typically be run on the result of the communicate() method
    of a subprocess.Popen object.
    """
    stderr = re.sub(br"\[\d+ refs, \d+ blocks\]\r?\n?", b"", stderr).strip()
    return stderr


# Cached result of the expensive test performed in the function below.
__cached_interp_requires_environment = None

def interpreter_requires_environment():
    """
    Returns True if our sys.executable interpreter requires environment
    variables in order to be able to run at all.
    This is designed to be used with @unittest.skipIf() to annotate tests
    that need to use an assert_python*() function to launch an isolated
    mode (-I) or no environment mode (-E) sub-interpreter process.
    A normal build & test does not run into this situation but it can happen
    when trying to run the standard library test suite from an interpreter that
    doesn't have an obvious home with Python's current home finding logic.
    Setting PYTHONHOME is one way to get most of the testsuite to run in that
    situation.  PYTHONPATH or PYTHONUSERSITE are other common environment
    variables that might impact whether or not the interpreter can start.
    """
    global __cached_interp_requires_environment
    if __cached_interp_requires_environment is None:
        # Try running an interpreter with -E to see if it works or not.
        try:
            subprocess.check_call([sys.executable, '-E',
                                   '-c', 'import sys; sys.exit(0)'])
        except subprocess.CalledProcessError:
            __cached_interp_requires_environment = True
        else:
            __cached_interp_requires_environment = False

    return __cached_interp_requires_environment


_PythonRunResult = collections.namedtuple("_PythonRunResult",
                                          ("rc", "out", "err"))


# Executing the interpreter in a subprocess
def run_python_until_end(*args, **env_vars):
    env_required = interpreter_requires_environment()
    if '__isolated' in env_vars:
        isolated = env_vars.pop('__isolated')
    else:
        isolated = not env_vars and not env_required

    # XXX backport: "-X faulthandler" is unavailable in Python < 3.3.
    cmd_line = ([sys.executable] if sys.version_info < (3, 3) else
                [sys.executable, '-X', 'faulthandler'])

    if isolated:
        # isolated mode: ignore Python environment variables, ignore user
        # site-packages, and don't add the current directory to sys.path

        # XXX backport: "-I" is unavailable in Python < 3.4.
        if (3, 4) <= sys.version_info:
            cmd_line.append('-I')

    elif not env_vars and not env_required:
        # ignore Python environment variables
        cmd_line.append('-E')
    # Need to preserve the original environment, for in-place testing of
    # shared library builds.
    env = os.environ.copy()
    # But a special flag that can be set to override -- in this case, the
    # caller is responsible to pass the full environment.
    if env_vars.pop('__cleanenv', None):
        env = {}
    env.update(env_vars)
    cmd_line.extend(args)
    p = subprocess.Popen(cmd_line, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=env)
    try:
        out, err = p.communicate()
    finally:
        subprocess._cleanup()
        p.stdout.close()
        p.stderr.close()
    rc = p.returncode
    err = strip_python_stderr(err)
    return _PythonRunResult(rc, out, err), cmd_line

def _assert_python(expected_success, *args, **env_vars):
    res, cmd_line = run_python_until_end(*args, **env_vars)
    if (res.rc and expected_success) or (not res.rc and not expected_success):
        # Limit to 80 lines to ASCII characters
        maxlen = 80 * 100
        out, err = res.out, res.err
        if len(out) > maxlen:
            out = b'(... truncated stdout ...)' + out[-maxlen:]
        if len(err) > maxlen:
            err = b'(... truncated stderr ...)' + err[-maxlen:]
        out = out.decode('ascii', 'replace').rstrip()
        err = err.decode('ascii', 'replace').rstrip()
        raise AssertionError("Process return code is %d\n"
                             "command line: %r\n"
                             "\n"
                             "stdout:\n"
                             "---\n"
                             "%s\n"
                             "---\n"
                             "\n"
                             "stderr:\n"
                             "---\n"
                             "%s\n"
                             "---"
                             % (res.rc, cmd_line,
                                out,
                                err))
    return res

def assert_python_ok(*args, **env_vars):
    """
    Assert that running the interpreter with `args` and optional environment
    variables `env_vars` succeeds (rc == 0) and return a (return code, stdout,
    stderr) tuple.
    If the __cleanenv keyword is set, env_vars is used as a fresh environment.
    Python is started in isolated mode (command line option -I),
    except if the __isolated keyword is set to False.
    """
    return _assert_python(True, *args, **env_vars)
