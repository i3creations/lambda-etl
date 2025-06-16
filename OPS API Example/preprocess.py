import numpy as np
import pandas as pd
from datetime import datetime
from field_names import field_names
from new_fileds import new_fileds
from MLStripper import strip_tags

def preprocess(data: str, last_run: datetime) -> pd.DataFrame:
  # Read data into Dataframe.
  df = pd.DataFrame(data)[[
    'Incident_Id',
    'SIR_',
    'Local_Date_Reported',
    'Facility_Address_HELPER',
    'Facility_Latitude',
    'Facility_Longitude',
    'Date_SIR_Processed__NT',
    'Details',
    'Section_5__Action_Taken',
    'Type_of_SIR',
    'Category_Type',
    'Sub_Category_Type'
  ]].set_index('Incident_Id')

  # Filter for valid SIRs that have been processed by the command center since
  # the last run.
  df = df.loc[
    (df['SIR_'] != 'REJECTED')
    & (~df['Date_SIR_Processed__NT'].isnull())
    & (pd.to_datetime(df['Local_Date_Reported']) < last_run) # INVERT
  ]

  # List columns to explode.
  cols = [
    'Type_of_SIR',
    'Category_Type',
    'Sub_Category_Type'
  ]

  for col in cols:
    df = df.explode(col)

  # Map Category/Type/Subtype to OPS Category/Type/Subtype/Sharing Level.
  # Will only keep those SIRs tracked in OPS.
  df = pd.merge(
    df,
    pd.read_csv('map.csv'),
    on = ['Type_of_SIR', 'Category_Type', 'Sub_Category_Type']
  )

  # List columns to strip HTML tags.
  cols = [
    'Details',
    'Section_5__Action_Taken'
  ]

  for col in cols:
    df[col] = df[col].apply(strip_tags)

  # Add Columns
  df['title'] = '[' + df['SIR_'] + ']: ' + df['Type_of_SIR']
  df['incidentReportDetails'] = (
    df['Details'] + '\n' + df['Section_5__Action_Taken']
  )
  for key in new_fileds:
    df[key] = new_fileds[key]

  # List columns to process datetime format.
  cols = [
    'Local_Date_Reported',
    'Date_SIR_Processed__NT'
  ]

  for col in cols:
    df[col] = pd.to_datetime(
      df[col],
      utc = True
    ).dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

  # List columns to convert to string.
  cols = [
    'Facility_Latitude',
    'Facility_Longitude'
  ]

  for col in cols:
    df[col] = df[col].astype(str)
  
  # Rename Columns
  df = df.reset_index().rename(
    columns = field_names
  ).replace({np.nan: None})

  # Drop Columns
  df = df.drop(
    ['index', 'Details', 'Section_5__Action_Taken', 'Type_of_SIR',
     'Category_Type', 'Sub_Category_Type', 'category'],
    axis = 1
  )

  return df