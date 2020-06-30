# -*- coding: UTF-8 -*-
"""
Created on 28.12.2012

@author: root
"""
import fnmatch
import os
import re
import shutil


def str_from_file(file_name):
    a_file = open(file_name, encoding='cp1250')
    out = a_file.read()
    a_file.close()
    return out


def str_to_file(string, file_name):
    a_file = open(file_name, encoding='cp1250', mode='w')
    a_file.write(string)
    a_file.close()


def str_set_to_file(full_file_name, str_header, set_of_strings):
    # is result - write to file
    if len(set_of_strings) > 0:
        a_file = open(full_file_name, encoding='cp1250', mode='w')
        if len(str_header) > 0:
            a_file.write(str_header + '\n')
            ## pretriditimport locale
            sorted_list = sorted(set_of_strings)
            for line in sorted_list:
                a_file.write(line + "\n")
        print("Write to file:" + full_file_name + " Number of lines:" + str(len(set_of_strings)))
        a_file.close()


def find_files(dir_name, fmask):
    includes = [fmask]  # for files only
    includes = r'|'.join([fnmatch.translate(x) for x in includes])
    ret_list = []
    try:
        for item in os.listdir(dir_name):
            if os.path.isfile(os.path.join(dir_name, item)):
                if re.match(includes, item):
                    ret_list.append(os.path.join(dir_name, item))
    except (FileNotFoundError):
        pass
    return ret_list


def get_backup_filename(backuped_file_name):
    """return name of first unused backup of given file - filename.000, filename.001, ..."""
    counter = 0
    filename = f"{backuped_file_name}.{counter:03}.bkp"
    while os.path.isfile(filename):
        counter += 1
        filename = f"{backuped_file_name}.{counter:03}.bkp"
    return filename


def copy_file(src, dest):
    shutil.copy(src, dest)


def backup_file(bck_fname):
    backup_fname = get_backup_filename(bck_fname)
    copy_file(bck_fname, backup_fname)
