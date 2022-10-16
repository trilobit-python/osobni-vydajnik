# -------------------------------------------------------------
#    rmblanks.py
#      Deletes all empty folders under a given path.
#    http://metinsaylan.com
# -------------------------------------------------------------

#    Usage: rmblanks.py "E:/Test"

import os
import shutil
import stat
import sys


def remove_readonly(fn, path):
    try:
        os.chmod(path, stat.S_IWRITE)
        fn(path)
    except Exception as exc:
        print(f'Skipped:{path} because:{exc}')


if len(sys.argv) == 1:
    # Print usage
    print("Usage: rmblanks.py \"E:/TestFolder\"")
else:
    for root, dirs, files in os.walk(sys.argv[1], topdown=False):
        for name in dirs:
            try:
                if len(os.listdir(os.path.join(root, name))) == 0:  # check whether the directory is empty
                    dir_path = os.path.join(root, name)
                    print("Deleting", dir_path)
                    try:
                        shutil.rmtree(dir_path, onerror=remove_readonly)
                    except (ValueError, Exception):
                        print("FAILED :")
            except (ValueError, Exception):
                pass
