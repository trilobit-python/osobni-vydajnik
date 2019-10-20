from src.readers.base_reader import xReader
from src.readers.mbank_bezny_ucet import mBank_bezny_ucet


class mBank_podnikani_ucet(mBank_bezny_ucet):
    def __init__(self, session, root_dir_trans_hist):
        xReader.__init__(self, session, 'podnikatelský účet mBank',
                         root_dir_trans_hist, r'mbank', 'mKonto_Business_15069717_*.csv')

    # -------------  funkčnost implementována v rodič. třídě