from datetime import datetime
from ops_api.processing.html_stripper import strip_tags
from ops_api.processing.field_mapping import get_field_mapping, map_field_name
from ops_api.processing.default_fields import get_default_fields, get_default_value
from ops_api.processing.preprocess import preprocess

class TestProcessing:

    def test_html_stripper(self):
        html = '<p>test</p><br />'
        assert strip_tags(html) == 'test'

    def test_get_field_mapping(self):
        assert len(get_field_mapping()) != 0
        assert map_field_name('SIR_') == 'tenantItemID'
        assert map_field_name('invalid') == 'invalid'

    def test_default_fields(self):
        assert len(get_default_fields()) != 0
        assert get_default_value('phase') == 'Monitored'
        assert get_default_value('invalid') == None