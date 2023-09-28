# coding: utf-8
from sqlalchemy import Column, Index, Integer, Numeric, Table, Text, UniqueConstraint, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


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
    INITIALBAL = Column(Numeric)
    FAVORITEACCT = Column(Text, nullable=False)
    CURRENCYID = Column(Integer, nullable=False)
    STATEMENTLOCKED = Column(Integer)
    STATEMENTDATE = Column(Text)
    MINIMUMBALANCE = Column(Numeric)
    CREDITLIMIT = Column(Numeric)
    INTERESTRATE = Column(Numeric)
    PAYMENTDUEDATE = Column(Text)
    MINIMUMPAYMENT = Column(Numeric)
    INITIALDATE = Column(Text)


class ASSETSV1(Base):
    __tablename__ = 'ASSETS_V1'

    ASSETID = Column(Integer, primary_key=True)
    STARTDATE = Column(Text, nullable=False)
    ASSETNAME = Column(Text, nullable=False)
    VALUE = Column(Numeric)
    VALUECHANGE = Column(Text)
    NOTES = Column(Text)
    VALUECHANGERATE = Column(Numeric)
    ASSETTYPE = Column(Text, index=True)
    ASSETSTATUS = Column(Text)
    CURRENCYID = Column(Integer)
    VALUECHANGEMODE = Column(Text)


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
    TRANSAMOUNT = Column(Numeric, nullable=False)
    STATUS = Column(Text)
    TRANSACTIONNUMBER = Column(Text)
    NOTES = Column(Text)
    CATEGID = Column(Integer)
    TRANSDATE = Column(Text)
    FOLLOWUPID = Column(Integer)
    TOTRANSAMOUNT = Column(Numeric)
    REPEATS = Column(Integer)
    NEXTOCCURRENCEDATE = Column(Text)
    NUMOCCURRENCES = Column(Integer)


class BUDGETSPLITTRANSACTIONSV1(Base):
    __tablename__ = 'BUDGETSPLITTRANSACTIONS_V1'

    SPLITTRANSID = Column(Integer, primary_key=True)
    TRANSID = Column(Integer, nullable=False, index=True)
    CATEGID = Column(Integer)
    SPLITTRANSAMOUNT = Column(Numeric)
    NOTES = Column(Text)


class BUDGETTABLEV1(Base):
    __tablename__ = 'BUDGETTABLE_V1'

    BUDGETENTRYID = Column(Integer, primary_key=True)
    BUDGETYEARID = Column(Integer, index=True)
    CATEGID = Column(Integer)
    PERIOD = Column(Text, nullable=False)
    AMOUNT = Column(Numeric, nullable=False)
    NOTES = Column(Text)
    ACTIVE = Column(Integer)


class BUDGETYEARV1(Base):
    __tablename__ = 'BUDGETYEAR_V1'

    BUDGETYEARID = Column(Integer, primary_key=True)
    BUDGETYEARNAME = Column(Text, nullable=False, unique=True)


class CATEGORYV1(Base):
    __tablename__ = 'CATEGORY_V1'
    __table_args__ = (
        UniqueConstraint('CATEGNAME', 'PARENTID'),
        Index('IDX_CATEGORY_CATEGNAME_PARENTID', 'CATEGNAME', 'PARENTID')
    )

    CATEGID = Column(Integer, primary_key=True)
    CATEGNAME = Column(Text, nullable=False, index=True)
    ACTIVE = Column(Integer)
    PARENTID = Column(Integer)
    transfer_flag = Column(Integer, server_default=text("0"))


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
    TRANSAMOUNT = Column(Numeric, nullable=False)
    STATUS = Column(Text)
    TRANSACTIONNUMBER = Column(Text)
    NOTES = Column(Text)
    CATEGID = Column(Integer)
    TRANSDATE = Column(Text, index=True)
    FOLLOWUPID = Column(Integer)
    TOTRANSAMOUNT = Column(Numeric)
    SUPERTYPE = Column(Text(1))
    LASTUPDATEDTIME = Column(Text)
    DELETEDTIME = Column(Text)


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
    BASECONVRATE = Column(Numeric)
    CURRENCY_SYMBOL = Column(Text, nullable=False, unique=True)
    CURRENCY_TYPE = Column(Text)


class CURRENCYHISTORYV1(Base):
    __tablename__ = 'CURRENCYHISTORY_V1'
    __table_args__ = (
        UniqueConstraint('CURRENCYID', 'CURRDATE'),
        Index('IDX_CURRENCYHISTORY_CURRENCYID_CURRDATE', 'CURRENCYID', 'CURRDATE')
    )

    CURRHISTID = Column(Integer, primary_key=True)
    CURRENCYID = Column(Integer, nullable=False)
    CURRDATE = Column(Text, nullable=False)
    CURRVALUE = Column(Numeric, nullable=False)
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
    NUMBER = Column(Text)
    WEBSITE = Column(Text)
    NOTES = Column(Text)
    ACTIVE = Column(Integer)
    PATTERN = Column(Text, server_default=text("''"))


class REPORTV1(Base):
    __tablename__ = 'REPORT_V1'

    REPORTID = Column(Integer, primary_key=True)
    REPORTNAME = Column(Text, nullable=False, unique=True)
    GROUPNAME = Column(Text)
    SQLCONTENT = Column(Text)
    LUACONTENT = Column(Text)
    TEMPLATECONTENT = Column(Text)
    DESCRIPTION = Column(Text)
    ACTIVE = Column(Integer)


class SETTINGV1(Base):
    __tablename__ = 'SETTING_V1'

    SETTINGID = Column(Integer, primary_key=True)
    SETTINGNAME = Column(Text, nullable=False, unique=True)
    SETTINGVALUE = Column(Text)


class SHAREINFOV1(Base):
    __tablename__ = 'SHAREINFO_V1'

    SHAREINFOID = Column(Integer, primary_key=True)
    CHECKINGACCOUNTID = Column(Integer, nullable=False, index=True)
    SHARENUMBER = Column(Numeric)
    SHAREPRICE = Column(Numeric)
    SHARECOMMISSION = Column(Numeric)
    SHARELOT = Column(Text)


class SPLITTRANSACTIONSV1(Base):
    __tablename__ = 'SPLITTRANSACTIONS_V1'

    SPLITTRANSID = Column(Integer, primary_key=True)
    TRANSID = Column(Integer, nullable=False, index=True)
    CATEGID = Column(Integer)
    SPLITTRANSAMOUNT = Column(Numeric)
    NOTES = Column(Text)


class STOCKHISTORYV1(Base):
    __tablename__ = 'STOCKHISTORY_V1'
    __table_args__ = (
        UniqueConstraint('SYMBOL', 'DATE'),
    )

    HISTID = Column(Integer, primary_key=True)
    SYMBOL = Column(Text, nullable=False, index=True)
    DATE = Column(Text, nullable=False)
    VALUE = Column(Numeric, nullable=False)
    UPDTYPE = Column(Integer)


class STOCKV1(Base):
    __tablename__ = 'STOCK_V1'

    STOCKID = Column(Integer, primary_key=True)
    HELDAT = Column(Integer, index=True)
    PURCHASEDATE = Column(Text, nullable=False)
    STOCKNAME = Column(Text, nullable=False)
    SYMBOL = Column(Text)
    NUMSHARES = Column(Numeric)
    PURCHASEPRICE = Column(Numeric, nullable=False)
    NOTES = Column(Text)
    CURRENTPRICE = Column(Numeric, nullable=False)
    VALUE = Column(Numeric)
    COMMISSION = Column(Numeric)


class TRANSLINKV1(Base):
    __tablename__ = 'TRANSLINK_V1'
    __table_args__ = (
        Index('IDX_LINKRECORD', 'LINKTYPE', 'LINKRECORDID'),
    )

    TRANSLINKID = Column(Integer, primary_key=True)
    CHECKINGACCOUNTID = Column(Integer, nullable=False, index=True)
    LINKTYPE = Column(Text, nullable=False)
    LINKRECORDID = Column(Integer, nullable=False)


class USAGEV1(Base):
    __tablename__ = 'USAGE_V1'

    USAGEID = Column(Integer, primary_key=True)
    USAGEDATE = Column(Text, nullable=False, index=True)
    JSONCONTENT = Column(Text, nullable=False)


t_android_metadata = Table(
    'android_metadata', metadata,
    Column('locale', Text)
)


t_v_SUPER_CHECKINGACCOUNT = Table(
    'v_SUPER_CHECKINGACCOUNT', metadata,
    Column('ST_PRIJEM', NullType),
    Column('ST_VYDAJ', NullType),
    Column('ST_INVESTICE', NullType),
    Column('ST_PREVOD', NullType),
    Column('TRANSFER_FLAG', Integer),
    Column('TRANSID', Integer),
    Column('ACCOUNTID', Integer),
    Column('TOACCOUNTID', Integer),
    Column('PAYEEID', Integer),
    Column('TRANSCODE', Text),
    Column('TRANSAMOUNT', Numeric),
    Column('STATUS', Text),
    Column('TRANSACTIONNUMBER', Text),
    Column('NOTES', Text),
    Column('CATEGID', Integer),
    Column('TRANSDATE', Text),
    Column('FOLLOWUPID', Integer),
    Column('TOTRANSAMOUNT', Numeric),
    Column('SUPERTYPE', Text(1)),
    Column('LASTUPDATEDTIME', Text),
    Column('DELETEDTIME', Text),
    Column('CATEGNAME', NullType)
)


t_v_SUPER_statistika_po_letech = Table(
    'v_SUPER_statistika_po_letech', metadata,
    Column('Rok', NullType),
    Column('CATEGNAME', Text),
    Column('SumCastka', NullType),
    Column('SumPrijem', NullType),
    Column('SumVyber', NullType),
    Column('SumPrevod', NullType),
    Column('SumaAmount', NullType),
    Column('CATEGID', Integer),
    Column('Pocet', NullType)
)


t_v_account_overview = Table(
    'v_account_overview', metadata,
    Column('ACCOUNTNAME', Text),
    Column('STATUS', Text),
    Column('ACCOUNTTYPE', Text),
    Column('first_trans', NullType),
    Column('last_trans', NullType),
    Column('count_trans', NullType),
    Column('NOTES', Text)
)


t_v_asi_duplicity = Table(
    'v_asi_duplicity', metadata,
    Column('ACCOUNTID', Integer),
    Column('TRANSDATE', Text),
    Column('TRANSCODE', Text),
    Column('TRANSAMOUNT', Numeric),
    Column('NOTES', Text),
    Column('Pocet', NullType)
)


t_v_category_usage = Table(
    'v_category_usage', metadata,
    Column('CATEGNAME', Text),
    Column('SumCastka', NullType),
    Column('SumPrijem', NullType),
    Column('SumVyber', NullType),
    Column('SumPrevod', NullType),
    Column('SumaAmount', NullType),
    Column('CATEGID', Integer),
    Column('Pocet', NullType)
)


t_v_checkingaccount_bez_kategorie = Table(
    'v_checkingaccount_bez_kategorie', metadata,
    Column('TRANSID', Integer),
    Column('ACCOUNTID', Integer),
    Column('TOACCOUNTID', Integer),
    Column('PAYEEID', Integer),
    Column('TRANSCODE', Text),
    Column('TRANSAMOUNT', Numeric),
    Column('STATUS', Text),
    Column('TRANSACTIONNUMBER', Text),
    Column('NOTES', Text),
    Column('CATEGID', Integer),
    Column('TRANSDATE', Text),
    Column('FOLLOWUPID', Integer),
    Column('TOTRANSAMOUNT', Numeric),
    Column('SUPERTYPE', Text(1)),
    Column('LASTUPDATEDTIME', Text),
    Column('DELETEDTIME', Text)
)


t_v_cte_category = Table(
    'v_cte_category', metadata,
    Column('CATEGID', Integer),
    Column('CATEGNAME', NullType),
    Column('ACTIVE', Integer),
    Column('PARENTID', Integer),
    Column('TRANSFER_FLAG', Integer)
)


t_v_ext_CHECKINGACCOUNT = Table(
    'v_ext_CHECKINGACCOUNT', metadata,
    Column('CASTKA', NullType),
    Column('PRIJEM', NullType),
    Column('VYBER', NullType),
    Column('PREVOD', NullType),
    Column('transfer_flag', Integer),
    Column('TRANSID', Integer),
    Column('ACCOUNTID', Integer),
    Column('TOACCOUNTID', Integer),
    Column('PAYEEID', Integer),
    Column('TRANSCODE', Text),
    Column('TRANSAMOUNT', Numeric),
    Column('STATUS', Text),
    Column('TRANSACTIONNUMBER', Text),
    Column('NOTES', Text),
    Column('CATEGID', Integer),
    Column('TRANSDATE', Text),
    Column('FOLLOWUPID', Integer),
    Column('TOTRANSAMOUNT', Numeric),
    Column('SUPERTYPE', Text(1)),
    Column('LASTUPDATEDTIME', Text),
    Column('DELETEDTIME', Text),
    Column('CATEGNAME', Text)
)


t_v_prijmy_bezny_mbank_po_letech = Table(
    'v_prijmy_bezny_mbank_po_letech', metadata,
    Column('ROK', NullType),
    Column('Pocet', NullType),
    Column('SumCastka', NullType),
    Column('CATEGID', Integer),
    Column('CATEGNAME', Text)
)


t_v_statistika_bez_kategorie = Table(
    'v_statistika_bez_kategorie', metadata,
    Column('NOTES', Text),
    Column('Pocet', NullType),
    Column('SumCastka', NullType),
    Column('MinDate', NullType),
    Column('MaxDate', NullType)
)


t_v_statistika_po_letech = Table(
    'v_statistika_po_letech', metadata,
    Column('Rok', NullType),
    Column('CATEGNAME', Text),
    Column('SumCastka', NullType),
    Column('SumPrijem', NullType),
    Column('SumVyber', NullType),
    Column('SumPrevod', NullType),
    Column('SumaAmount', NullType),
    Column('CATEGID', Integer),
    Column('Pocet', NullType)
)


t_v_subcategory_usage = Table(
    'v_subcategory_usage', metadata,
    Column('CATEGNAME', Text),
    Column('SumCastka', NullType),
    Column('SumPrijem', NullType),
    Column('SumVyber', NullType),
    Column('SumPrevod', NullType),
    Column('SumaAmount', NullType),
    Column('CATEGID', Integer),
    Column('Pocet', NullType)
)


t_v_summary = Table(
    'v_summary', metadata,
    Column('ROK', NullType),
    Column('SumCastka', NullType),
    Column('SumPrijem', NullType),
    Column('SumVyber', NullType),
    Column('SumPrevod', NullType),
    Column('Pocet', NullType)
)


t_v_summary_bez_prevodu = Table(
    'v_summary_bez_prevodu', metadata,
    Column('ROK', NullType),
    Column('Pocet', NullType),
    Column('SumCastka', NullType),
    Column('TRANSCODE', Text)
)
