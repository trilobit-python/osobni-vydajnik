# coding: utf-8
from sqlalchemy import Column, Float, Index, Integer, Text, UniqueConstraint
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base

from src.sqlite.sqlite_numeric import SqliteNumeric

Numeric = SqliteNumeric

Base = declarative_base()

class Serializer(object):

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]

class ACCOUNTLISTV1(Base):
    __tablename__ = 'ACCOUNTLIST_V1'

    ACCOUNTID = Column(Integer, primary_key=True)
    ACCOUNTNAME = Column(Text, nullable=False, unique=True)
    ACCOUNTTYPE = Column(Text, nullable=False, index=True)
    ACCOUNTNUM = Column(Text)
    STATUS = Column(Text, nullable=False)
    NOTES = Column(Text)
    HELDAT = Column(Text)
    WEBSITE = Column(Text)
    CONTACTINFO = Column(Text)
    ACCESSINFO = Column(Text)
    INITIALBAL = Column(SqliteNumeric)
    FAVORITEACCT = Column(Text, nullable=False)
    CURRENCYID = Column(Integer, nullable=False)
    STATEMENTLOCKED = Column(Integer)
    STATEMENTDATE = Column(Text)
    MINIMUMBALANCE = Column(SqliteNumeric)
    CREDITLIMIT = Column(SqliteNumeric)
    INTERESTRATE = Column(SqliteNumeric)
    PAYMENTDUEDATE = Column(Text)
    MINIMUMPAYMENT = Column(SqliteNumeric)


class ASSETCLASSSTOCKV1(Base):
    __tablename__ = 'ASSETCLASS_STOCK_V1'

    ID = Column(Integer, primary_key=True)
    ASSETCLASSID = Column(Integer, nullable=False)
    STOCKSYMBOL = Column(Text)

class ASSETCLASSV1(Base):
    __tablename__ = 'ASSETCLASS_V1'

    ID = Column(Integer, primary_key=True)
    PARENTID = Column(Integer)
    NAME = Column(Text, nullable=False)
    ALLOCATION = Column(Float)
    SORTORDER = Column(Integer)


class ASSETSV1(Base):
    __tablename__ = 'ASSETS_V1'

    ASSETID = Column(Integer, primary_key=True)
    STARTDATE = Column(Text, nullable=False)
    ASSETNAME = Column(Text, nullable=False)
    VALUE = Column(SqliteNumeric)
    VALUECHANGE = Column(Text)
    NOTES = Column(Text)
    VALUECHANGERATE = Column(SqliteNumeric)
    ASSETTYPE = Column(Text, index=True)


class ATTACHMENTV1(Base):
    __tablename__ = 'ATTACHMENT_V1'
    __table_args__ = (
        Index('IDX_ATTACHMENT_REF', 'REFTYPE', 'REFID'),
    )

    ATTACHMENTID = Column(Integer, primary_key=True)
    REFTYPE = Column(Text, nullable=False)
    REFID = Column(Integer, nullable=False)
    DESCRIPTION = Column(Text)
    FILENAME = Column(Text, nullable=False)


class BILLSDEPOSITSV1(Base):
    __tablename__ = 'BILLSDEPOSITS_V1'
    __table_args__ = (
        Index('IDX_BILLSDEPOSITS_ACCOUNT', 'ACCOUNTID', 'TOACCOUNTID'),
    )

    BDID = Column(Integer, primary_key=True)
    ACCOUNTID = Column(Integer, nullable=False)
    TOACCOUNTID = Column(Integer)
    PAYEEID = Column(Integer, nullable=False)
    TRANSCODE = Column(Text, nullable=False)
    TRANSAMOUNT = Column(SqliteNumeric, nullable=False)
    STATUS = Column(Text)
    TRANSACTIONNUMBER = Column(Text)
    NOTES = Column(Text)
    CATEGID = Column(Integer)
    SUBCATEGID = Column(Integer)
    TRANSDATE = Column(Text)
    FOLLOWUPID = Column(Integer)
    TOTRANSAMOUNT = Column(SqliteNumeric)
    REPEATS = Column(Integer)
    NEXTOCCURRENCEDATE = Column(Text)
    NUMOCCURRENCES = Column(Integer)


class BUDGETSPLITTRANSACTIONSV1(Base):
    __tablename__ = 'BUDGETSPLITTRANSACTIONS_V1'

    SPLITTRANSID = Column(Integer, primary_key=True)
    TRANSID = Column(Integer, nullable=False, index=True)
    CATEGID = Column(Integer)
    SUBCATEGID = Column(Integer)
    SPLITTRANSAMOUNT = Column(SqliteNumeric)


class BUDGETTABLEV1(Base):
    __tablename__ = 'BUDGETTABLE_V1'

    BUDGETENTRYID = Column(Integer, primary_key=True)
    BUDGETYEARID = Column(Integer, index=True)
    CATEGID = Column(Integer)
    SUBCATEGID = Column(Integer)
    PERIOD = Column(Text, nullable=False)
    AMOUNT = Column(SqliteNumeric, nullable=False)


class BUDGETYEARV1(Base):
    __tablename__ = 'BUDGETYEAR_V1'

    BUDGETYEARID = Column(Integer, primary_key=True)
    BUDGETYEARNAME = Column(Text, nullable=False, unique=True)


class CATEGORYV1(Base):
    __tablename__ = 'CATEGORY_V1'

    CATEGID = Column(Integer, primary_key=True)
    CATEGNAME = Column(Text, nullable=False, unique=True)


# class CHECKINGACCOUNTV1(Base, Serializer):
#     __tablename__ = 'CHECKINGACCOUNT_V1'
#     __table_args__ = (
#         Index('IDX_CHECKINGACCOUNT_ACCOUNT', 'ACCOUNTID', 'TOACCOUNTID'),
#     )
#
#     TRANSID = Column(Integer, primary_key=True)
#     ACCOUNTID = Column(Integer, nullable=False)
#     TOACCOUNTID = Column(Integer)
#     PAYEEID = Column(Integer, nullable=False)
#     TRANSCODE = Column(Text, nullable=False)
#     TRANSAMOUNT = Column(Numeric(12, 2), nullable=False)
#     STATUS = Column(Text)
#     TRANSACTIONNUMBER = Column(Text)
#     NOTES = Column(Text)
#     CATEGID = Column(Integer)
#     SUBCATEGID = Column(Integer)
#     TRANSDATE = Column(Text, index=True)
#     FOLLOWUPID = Column(Integer)
#     TOTRANSAMOUNT = Column(Numeric(12, 2))
#
#     def serialize(self):
#         d = Serializer.serialize(self)
#         return d

class CHECKINGACCOUNTV1(Base):
    __tablename__ = 'CHECKINGACCOUNT_V1'
    __table_args__ = (
        Index('IDX_CHECKINGACCOUNT_ACCOUNT', 'ACCOUNTID', 'TOACCOUNTID'),
    )

    TRANSID = Column(Integer, primary_key=True)
    ACCOUNTID = Column(Integer, nullable=False)
    TOACCOUNTID = Column(Integer)
    PAYEEID = Column(Integer, nullable=False)
    TRANSCODE = Column(Text, nullable=False)
    TRANSAMOUNT = Column(SqliteNumeric, nullable=False)
    STATUS = Column(Text)
    TRANSACTIONNUMBER = Column(Text)
    NOTES = Column(Text)
    CATEGID = Column(Integer)
    SUBCATEGID = Column(Integer)
    TRANSDATE = Column(Text, index=True)
    FOLLOWUPID = Column(Integer)
    TOTRANSAMOUNT = Column(SqliteNumeric)
    SUPERTYPE = Column(Text)

class CURRENCYFORMATSV1(Base):
    __tablename__ = 'CURRENCYFORMATS_V1'

    CURRENCYID = Column(Integer, primary_key=True)
    CURRENCYNAME = Column(Text, nullable=False, unique=True)
    PFX_SYMBOL = Column(Text)
    SFX_SYMBOL = Column(Text)
    DECIMAL_POINT = Column(Text)
    GROUP_SEPARATOR = Column(Text)
    UNIT_NAME = Column(Text)
    CENT_NAME = Column(Text)
    SCALE = Column(Integer)
    BASECONVRATE = Column(SqliteNumeric)
    CURRENCY_SYMBOL = Column(Text, nullable=False, index=True)


class CURRENCYHISTORYV1(Base):
    __tablename__ = 'CURRENCYHISTORY_V1'
    __table_args__ = (
        UniqueConstraint('CURRENCYID', 'CURRDATE'),
        Index('IDX_CURRENCYHISTORY_CURRENCYID_CURRDATE', 'CURRENCYID', 'CURRDATE')
    )

    CURRHISTID = Column(Integer, primary_key=True)
    CURRENCYID = Column(Integer, nullable=False)
    CURRDATE = Column(Text, nullable=False)
    CURRVALUE = Column(SqliteNumeric, nullable=False)
    CURRUPDTYPE = Column(Integer)


class CUSTOMFIELDDATAV1(Base):
    __tablename__ = 'CUSTOMFIELDDATA_V1'
    __table_args__ = (
        UniqueConstraint('FIELDID', 'REFID'),
        Index('IDX_CUSTOMFIELDDATA_REF', 'FIELDID', 'REFID')
    )

    FIELDATADID = Column(Integer, primary_key=True)
    FIELDID = Column(Integer, nullable=False)
    REFID = Column(Integer, nullable=False)
    CONTENT = Column(Text)


class CUSTOMFIELDV1(Base):
    __tablename__ = 'CUSTOMFIELD_V1'

    FIELDID = Column(Integer, primary_key=True)
    REFTYPE = Column(Text, nullable=False, index=True)
    DESCRIPTION = Column(Text)
    TYPE = Column(Text, nullable=False)
    PROPERTIES = Column(Text, nullable=False)


class INFOTABLEV1(Base):
    __tablename__ = 'INFOTABLE_V1'

    INFOID = Column(Integer, primary_key=True)
    INFONAME = Column(Text, nullable=False, unique=True)
    INFOVALUE = Column(Text, nullable=False)


class PAYEEV1(Base):
    __tablename__ = 'PAYEE_V1'

    PAYEEID = Column(Integer, primary_key=True)
    PAYEENAME = Column(Text, nullable=False, unique=True)
    CATEGID = Column(Integer)
    SUBCATEGID = Column(Integer)


class REPORTV1(Base):
    __tablename__ = 'REPORT_V1'

    REPORTID = Column(Integer, primary_key=True)
    REPORTNAME = Column(Text, nullable=False, unique=True)
    GROUPNAME = Column(Text)
    SQLCONTENT = Column(Text)
    LUACONTENT = Column(Text)
    TEMPLATECONTENT = Column(Text)
    DESCRIPTION = Column(Text)


class SETTINGV1(Base):
    __tablename__ = 'SETTING_V1'

    SETTINGID = Column(Integer, primary_key=True)
    SETTINGNAME = Column(Text, nullable=False, unique=True)
    SETTINGVALUE = Column(Text)


class SHAREINFOV1(Base):
    __tablename__ = 'SHAREINFO_V1'

    SHAREINFOID = Column(Integer, primary_key=True)
    CHECKINGACCOUNTID = Column(Integer, nullable=False, index=True)
    SHARENUMBER = Column(SqliteNumeric)
    SHAREPRICE = Column(SqliteNumeric)
    SHARECOMMISSION = Column(SqliteNumeric)
    SHARELOT = Column(Text)


class SPLITTRANSACTIONSV1(Base):
    __tablename__ = 'SPLITTRANSACTIONS_V1'

    SPLITTRANSID = Column(Integer, primary_key=True)
    TRANSID = Column(Integer, nullable=False, index=True)
    CATEGID = Column(Integer)
    SUBCATEGID = Column(Integer)
    SPLITTRANSAMOUNT = Column(SqliteNumeric)


class STOCKHISTORYV1(Base):
    __tablename__ = 'STOCKHISTORY_V1'
    __table_args__ = (
        UniqueConstraint('SYMBOL', 'DATE'),
    )

    HISTID = Column(Integer, primary_key=True)
    SYMBOL = Column(Text, nullable=False, index=True)
    DATE = Column(Text, nullable=False)
    VALUE = Column(SqliteNumeric, nullable=False)
    UPDTYPE = Column(Integer)


class STOCKV1(Base):
    __tablename__ = 'STOCK_V1'

    STOCKID = Column(Integer, primary_key=True)
    HELDAT = Column(Integer, index=True)
    PURCHASEDATE = Column(Text, nullable=False)
    STOCKNAME = Column(Text, nullable=False)
    SYMBOL = Column(Text)
    NUMSHARES = Column(SqliteNumeric)
    PURCHASEPRICE = Column(SqliteNumeric, nullable=False)
    NOTES = Column(Text)
    CURRENTPRICE = Column(SqliteNumeric, nullable=False)
    VALUE = Column(SqliteNumeric)
    COMMISSION = Column(SqliteNumeric)


class SUBCATEGORYV1(Base):
    __tablename__ = 'SUBCATEGORY_V1'
    __table_args__ = (
        UniqueConstraint('CATEGID', 'SUBCATEGNAME'),
    )

    SUBCATEGID = Column(Integer, primary_key=True)
    SUBCATEGNAME = Column(Text, nullable=False)
    CATEGID = Column(Integer, nullable=False, index=True)





