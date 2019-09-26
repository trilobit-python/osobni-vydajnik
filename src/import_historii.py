#!/usr/bin/env python
# -*- coding: windows-1250 -*-
# -------------------------------------------------------------------------------
# Name:        importer transakcni historie do sqlite DB souboru aplikace MME MoneyManagerEx
# Author:      P3402617
# Created:     11/01/2016
# Copyright:   (c) P3402617
# -------------------------------------------------------------------------------

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from readers import Raiffeisen_sporici_ucet, Raiffeisen_bezny_ucet, mBank_bezny_ucet, Raiffeisen_cards
from sqlalchemy_declarative import Base

db_file = 'sqlite:///..//vydajeMMEX.mmb'
# engine = create_engine( db_file, echo=True)
engine = create_engine(db_file)

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
DBSession.configure(bind=engine)
session = DBSession()

# ----------- načítání
# airBank = airBankReader(session)
# airBank.read()

RB_karty = Raiffeisen_cards(session)
RB_karty.read()

# RB_sporici_ucet = Raiffeisen_sporici_ucet(session)
# RB_sporici_ucet.read()
#
# RB_bezny_ucet = Raiffeisen_bezny_ucet(session)
# RB_bezny_ucet.read()

# mBank_bezny = mBank_bezny_ucet(session)
# mBank_bezny.read()

# Anna_ucet_ERA = AnnaUcetEra(session)
# Anna_ucet_ERA.read()

# xcategoriser = categorizer(session)
# xcategoriser.set_all()

