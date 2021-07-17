import logging
import os

from lxml import etree

from odoo.loglevels import ustr
from odoo.tools import misc, view_validation

_logger = logging.getLogger(__name__)

_view_validator = None


@view_validation.validate('pin_map')
def schema_pin_map_view(arch, **kwargs):
    global _view_validator

    if _view_validator is None:
        with misc.file_open(os.path.join('syd_web_pin_map', 'views', 'pin_map.rng')) as f:
            _view_validator = etree.RelaxNG(etree.parse(f))

    if _view_validator.validate(arch):
        return True

    for error in _view_validator.error_log:
        _logger.error(ustr(error))
    return False
