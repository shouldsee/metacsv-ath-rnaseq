from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel
import pandas as pd

import subprocess
app = FastAPI()

from typing import Any,List
app.mount("/static", StaticFiles(directory="."), name="static")
class csvData(BaseModel):
	data:List[Any]
	type:str
	columns:List[str]
	gh_token: str = None

@app.post("/auto_pr")
async def auto_pull_request( dat:csvData):
	import os
	GH_TOKEN = os.environ.get('GH_TOKEN')
	df = pd.DataFrame( dat.data,None, dat.columns)
	df.head(5).to_csv('root.hand_patch.csv',index=0)
	# os.environ['HUB_VERBOSE']="1";
	subprocess.check_output(' '.join(['HUB_VERBOSE=1','bash','autopr.sh',GH_TOKEN]),shell=True)
