#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
import shutil

from common_utils import get_win_abs_path

src_file = get_win_abs_path(r'..\..\..\Apps\MoneyManagerEx Mobile\vydajeMMEX.mmb')
dst_file = 'vydajeMMEX.sqlite'

print('Copy file {} to {}'.format(src_file, dst_file))
shutil.copy2(src_file, dst_file)

