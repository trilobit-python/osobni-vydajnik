from src.readers.base_reader import xReader
from src.readers.rb_sporici_ucet import Raiffeisen_sporici_ucet


class Raiffeisen_bezny_ucet(Raiffeisen_sporici_ucet):
    def __init__(self, session, root_dir_trans_hist):
        xReader.__init__(self, session, 'Raiffeisen běžný účet',
                         root_dir_trans_hist, r'raiffeisenbank\new_fmt_2018', 'Pohyby_0646562002_*.csv')

    # -------------  funkčnost implementována v rodič. třídě