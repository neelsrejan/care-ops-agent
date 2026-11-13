import re,glob,hashlib,os,json
files=glob.glob('jds/*')+[f for f in glob.glob('to-apply/**/*',recursive=True) if os.path.isfile(f) and re.search(r'(jd|JD\.txt)',os.path.basename(f),re.I)]
docs={}
for f in files:
    if 'index' in f: continue
    t=open(f,errors='ignore').read()
    # dedupe .md/.txt pairs and copies by normalized stem
    k=re.sub(r'(_2)?\.(md|txt)$','',os.path.basename(f)).lower()
    if k in('jd','jd'): k=os.path.dirname(f).lower()
    docs[k]=docs.get(k,'')+' '+t
scr=glob.glob('runs/*screener*.md')
T={'Jira':r'\bjira\b','Asana':r'\basana\b','Smartsheet':r'smartsheet','Monday.com':r'monday\.com','ClickUp':r'clickup','MS Project':r'(ms|microsoft) project','Wrike':r'\bwrike\b','Airtable':r'airtable','Notion':r'\bnotion\b','Linear':r'\blinear\.app|\blinear \(|\blinear,','Confluence':r'confluence',
'Tableau':r'tableau','Power BI':r'power ?bi','Looker':r'\blooker\b','Hex':r'\bhex\b','Mode':r'\bmode analytics','Sigma (BI)':r'sigma computing',
'Snowflake':r'snowflake','BigQuery':r'bigquery','Databricks':r'databricks','SQL':r'\bsql\b','dbt':r'\bdbt\b','Python':r'\bpython\b','R':r'\bR\b(?=[ ,/)])',
'Salesforce':r'salesforce','HubSpot':r'hubspot','Zapier':r'zapier','Power Automate':r'power automate','n8n':r'\bn8n\b',
'Epic':r'\bepic\b(?! ?s\b)','FHIR/HL7':r'\bfhir\b|\bhl7\b','HEDIS':r'\bhedis\b','Cerner/Oracle Health':r'cerner|oracle health','Excel':r'\bexcel\b','Lean/Six Sigma':r'six sigma|\blean\b','Visio':r'\bvisio\b','Agile/Scrum':r'\bagile\b|\bscrum\b'}
def cnt(d):
    return {n:sum(1 for t in d if re.search(p,t,0 if n in('R',) else re.I)) for n,p in T.items()}
jd=cnt(list(docs.values())); sc=cnt([open(f,errors='ignore').read() for f in scr])
print(len(docs),len(scr))
for n in sorted(T,key=lambda n:-jd[n]): print(f'{n}|{jd[n]}|{sc[n]}')
