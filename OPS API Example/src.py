from opts.ArcherAuth import ArcherAuth
from log_time import log_time
from preprocess import preprocess
from send import send

last_run = log_time()

env = 'Test'
usr = ''
pwd = ''
url = 'https://optstest.uscis.dhs.gov/'

with ArcherAuth(env, usr, pwd, url) as asc:
  data = asc.get_levels_metadata(['Incidents'])

df = preprocess(data['Incidents'], last_run = last_run)

responses = send(df.to_dict('records')) # LOG THIS