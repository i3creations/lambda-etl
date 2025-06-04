import pytz
from datetime import datetime
from src.utils.time_utils import log_time, get_current_time, update_last_run_time, format_datetime, get_last_run_time
from src.utils.logging_utils import get_logger, log_exception, setup_logging

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
        
    def test_format_datetime(self):
        dt = pytz.timezone('US/Eastern').localize(datetime(2020, 1, 1, 12, 0, 0))
        formatted = format_datetime(dt)
        assert '2020-01-01T12:00:00' in formatted
        
    def test_get_last_run_time(self, tmpdir):
        file = tmpdir.join('time_log.txt')
        # Test with existing file
        file.write('2020-01-01T12:00:00-0500')
        last_time = get_last_run_time(file.strpath)
        assert last_time.year == 2020
        assert last_time.month == 1
        assert last_time.day == 1
        
        # Test with non-existent file
        non_existent = tmpdir.join('non_existent.txt')
        last_time = get_last_run_time(non_existent.strpath)
        assert last_time is not None  # Should return current time


    # Logger utils tests
    def test_logger(self):
        log = get_logger()
        assert log is not None
        assert log.name == 'src'
        
    def test_logger_with_name(self):
        log = get_logger('test_module')
        assert log is not None
        assert log.name == 'src.test_module'
        
    def test_log_exception(self):
        log = get_logger('test')
        # Test that log_exception doesn't raise an error
        try:
            log_exception(log, Exception('test exception'), 'test message')
            log_exception(log, Exception('test exception'))  # Without message
        except Exception as e:
            assert False, f"log_exception raised an exception: {e}"
            
    def test_setup_logging(self, tmpdir):
        log_file = tmpdir.join('test.log')
        logger = setup_logging(log_file=log_file.strpath)
        assert logger is not None
        assert logger.name == 'src'
        
        # Test without log file
        logger2 = setup_logging()
        assert logger2 is not None
