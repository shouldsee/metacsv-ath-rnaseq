import os
from path import Path
os.environ['GOOGLE_APPLICATION_CREDENTIALS']= Path('~/.ssh/gcp.json').expand()

from google.cloud import bigquery
client = bigquery.Client()


# query_job = client.query('''
# 	SELECT * 
# 	-- FROM `bigquery-public-data.stackoverflow`.INFORMATION_SCHEMA.COLUMNS
# 	FROM `nih-sra-datastore.sra`.INFORMATION_SCHEMA.COLUMNS
# 	-- LIMIT 10
# 	'''
# 	)

from pprint import pprint
import pandas as pd
pd.set_option("max_colwidth", -1)
pd.set_option('display.max_columns', None)


query_job = client.query('''
	SELECT *
	-- FROM `bigquery-public-data.stackoverflow`.INFORMATION_SCHEMA.COLUMNS
	FROM `nih-sra-datastore.sra`.metadata
	WHERE sample_acc in  ("SRR1005385","ERS214143","ERS214131","DRS007602","DRS007600","DRS007601")
	-- .INFORMATION_SCHEMA.COLUMNS
	LIMIT 10
	'''
	)


results = query_job.result().to_dataframe()  # Waits for job to complete.

df = results.to_dataframe()
df.to_html('temp_sql.html')
pprint(df)

