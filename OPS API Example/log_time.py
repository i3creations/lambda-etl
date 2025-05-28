import pytz
from datetime import datetime

def log_time() -> datetime:
  tz = pytz.timezone('US/Eastern')
  fmt = '%Y-%m-%dT%H:%M:%S%z'

  current_time = tz.localize(datetime.now())

  with open('time_log.txt', 'r+') as file:
      previous_time = datetime.strptime(file.read(), fmt)
      file.seek(0)
      file.write(current_time.strftime(fmt))

  return previous_time