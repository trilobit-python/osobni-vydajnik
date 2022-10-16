#
# aby se to dalo importovat jako modul
#

from .konstanty import CATEGID_NEZNAMA
from .category_setter import CategorySetter
from .base_writer import Writer

__all__ = ('Writer', 'CategorySetter', 'CATEGID_NEZNAMA',)
