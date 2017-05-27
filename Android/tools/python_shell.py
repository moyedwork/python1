"""Python shell on Android.

When python_shell.py is run without parameters, build a shell script, install it
with adb on Android and print a message explaining how to source the script in
order to set the environment variables.
When run with parameters, add to the shell script a statement to run python
with those parameters, install the script with adb and run the script on
Android in an adb shell session.
"""

import sys
import os
import string
import textwrap
import shutil
import subprocess

from android_utils import (adb_push_to_dir, run_script, AndroidError)

# Maximum file name size on nearly all current file systems.
MAX_FNAME_SIZE = 255
USAGE = """
===========================================================================

Set the environment by sourcing python_shell.sh with the following command:
    '. ${SYS_EXEC_PREFIX}/bin/python_shell.sh'

===========================================================================

"""

def build_script():
    script = """
        # Set the environment variables and change the current directory to
        # SYS_EXEC_PREFIX.
        export HOME=$ANDROID_APP_DIR
        export PATH=$SYS_EXEC_PREFIX/bin:$$PATH
        export LD_LIBRARY_PATH=$SYS_EXEC_PREFIX/lib
        export TERM=linux
        export TERMINFO=$SYS_EXEC_PREFIX/share/terminfo
        export INPUTRC=$SYS_EXEC_PREFIX/etc/inputrc
        cd $SYS_EXEC_PREFIX

    """
    script = textwrap.dedent(script)
    if len(sys.argv) == 1:
        script_name = 'python_shell.sh'

        # The adb shell starts up with an annoying 80 characters width, use
        # the current terminal width instead if available.
        os.environ['COLUMNS'] = str(shutil.get_terminal_size().columns)
        script += '# Set the terminal width.\n'
        script += 'export COLUMNS=$COLUMNS\n'
    else:
        args = ''.join(map(lambda c: c if c.isalnum() else '_',
                           '_'.join(sys.argv[1:])))
        s = 'python_%s.sh' % args
        l = len(s)
        if l > MAX_FNAME_SIZE:
            slice = MAX_FNAME_SIZE // 2 - 2
            s = s[:slice] + '____' + s[l - slice:]
        script_name = s
        script += 'python %s\n' % ' '.join(sys.argv[1:])

    script_path = os.path.join(os.environ['DIST_DIR'], script_name)
    with open(script_path, 'w') as f:
        f.write(string.Template(script).substitute(os.environ))
    os.chmod(script_path, 0o775)
    return script_path

def main():
    script_path = build_script()

    # The adb shell is mksh (The MirBSD Korn Shell) and it would be possible
    # to update its configuration file at /system/etc/mkshrc on Android to add
    # those environment variables by remounting /system read-write when root
    # access rights are available. It is more robust to ask the user to source
    # python_shell.sh instead.
    # See
    # http://stackoverflow.com/questions/11950131/android-adb-shell-ash-or-ksh.
    if len(sys.argv) == 1:
        bin_dir = os.path.join(os.environ['SYS_EXEC_PREFIX'], 'bin')
        adb_push_to_dir(script_path, bin_dir)
        print(string.Template(USAGE).substitute(os.environ))
    else:
        run_script(script_path)

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print('CalledProcessError: Command %(cmd)s: stdout=<%(output)s> '
               'stderr=<%(stderr)s>' % e.__dict__, file=sys.stderr)
        sys.exit(1)
    except AndroidError as e:
        sys.exit(e)
