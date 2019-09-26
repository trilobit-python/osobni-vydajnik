from decimal import Decimal as D

import sqlalchemy.types as types


class SqliteNumeric(types.TypeDecorator):
    impl = types.String
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))
    def process_bind_param(self, value, dialect):
        return str(value)
    def process_result_value(self, value, dialect):
        return D(value)

# can overwrite the imported type name
# @note: the TypeDecorator does not guarantie the scale and precision.
# you can do this with separate checks
# Numeric = SqliteNumeric
# class T(Base):
#     __tablename__ = 't'
#     id = Column(Integer, primary_key=True, nullable=False, unique=True)
#     value = Column(Numeric(12, 2), nullable=False)
#     #value = Column(SqliteNumeric(12, 2), nullable=False)
#
#     def __init__(self, value):
#         self.value = value


# class SqliteNumeric(types.TypeDecorator):
#     impl = types.String
#     def load_dialect_impl(self, dialect):
#         return dialect.type_descriptor(types.VARCHAR(100))
#     def process_bind_param(self, value, dialect):
#         return str(value)
#     def process_result_value(self, value, dialect):
#         try:
#             # print(value, type(value))
#             if type(value) is int:
#                 my_value = D(value)
#             elif type(value) is float:
#                 my_value = D(str(value))
#             elif type(value) is None:
#                 my_value = D(0)
#             elif value == 'None':
#                 my_value = D(0)
#             else:
#                 my_value = D(value)
#         except TypeError:
#             my_value = ''  # or whatever you want to do
#         return my_value

# can overwrite the imported type name
# @note: the TypeDecorator does not guarantie the scale and precision.
# you can do this with separate checks
# Numeric = SqliteNumeric
# class T(Base):
#     __tablename__ = 't'
#     id = Column(Integer, primary_key=True, nullable=False, unique=True)
#     value = Column(Numeric(12, 2), nullable=False)
#     #value = Column(SqliteNumeric(12, 2), nullable=False)
#
#     def __init__(self, value):
#         self.value = value
#
