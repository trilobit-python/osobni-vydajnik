import unittest

from setrid_tabulky import serad_tabulky


class MyTestCase(unittest.TestCase):
    def call_serad_tabulky(self, tabulky, zavislosti, ocekavany_vysledek, raise_exception):
        vysledek = serad_tabulky(tabulky, zavislosti)
        self.assertEqual(ocekavany_vysledek, vysledek)

    def test_something(self):
        self.call_serad_tabulky('t1,t2', '', 't1,t2')
        self.call_serad_tabulky('t1,t2,t3', 't1-t2,t2-t3', 't3,t1,t2')


if __name__ == '__main__':
    unittest.main()
