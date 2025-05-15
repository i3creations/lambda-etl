import pytz
from datetime import datetime
from ops_api.utils.time_utils import log_time, get_current_time, update_last_run_time
from ops_api.utils.logging_utils import get_logger, log_exception

class TestUtils:
    # Time Utils tests
    def test_time(self):
        curr_time = pytz.timezone('US/Eastern').localize(datetime.now()).strftime('%Y-%m-%dT%H')
        assert log_time().strftime('%Y-%m-%dT%H') <= curr_time

    def test_current_time(self):
        assert get_current_time().strftime('%Y-%m-%dT%H') >= pytz.timezone('US/Eastern').localize(datetime.now()).strftime('%Y-%m-%dT%H')

    def test_last_run_time(self, tmpdir):
        file = tmpdir.join('output.txt')
        update_last_run_time(file.strpath, datetime.strptime('01/01/20', '%m/%d/%y'))
        assert file.read() == '2020-01-01T00:00:00-0500'


    # Logger utils tests
    def test_loger(self):
        log = get_logger()
        log_exception(log, Exception,'test message')
        assert log