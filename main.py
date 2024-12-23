from urllib.request import Request, urlopen
from urllib.error import URLError
import sys
import json
import base64
import requests
from requests.auth import HTTPBasicAuth
import glob
import pandas as pd
import openpyxl
import demoji
import re
import io

JIRA_URL = "https://jira.atlassian.net"
JIRA_USERNAME = "JIRA User name"
JIRA_PASSWORD = "JIRA Token" 
JIRA_PROJECT_KEY = "project key"
JIRA_ISSUE_TYPE = "issue type"

def jira_rest_call(data):

    url = JIRA_URL + '/rest/api/2/issue'
    base64string = base64.b64encode(f'{JIRA_USERNAME}:{JIRA_PASSWORD}'.encode()).decode().replace('\n', '')

    restreq = Request(url, data.encode()) 
    restreq.add_header('Content-Type', 'application/json')
    restreq.add_header("Authorization", "Basic %s" % base64string)

    try:
        response = urlopen(restreq)
        return json.loads(response.read())
    except URLError as e:
        print(f"Failed to reach the server: {e.reason}")
        sys.exit()

def generate_summary(file_name):
    file_name = file_name.replace('.txt', '')
    file_name = file_name.replace('git-', '')
    return'['+(file_name).split('/')[-1]+ '] Hardcoded creds Found'
    
def generate_description(data):
    return "Sensitive Hardcoded Credetials found\n" 

def generate_issue_data(summary, description):

    json_data = json.dumps({
        "fields": {
            "project": {
                "key": JIRA_PROJECT_KEY
            },
            "summary": summary,
            "issuetype": {
                "name": JIRA_ISSUE_TYPE
            },
            "description": description
        }
    })
    return json_data


def add_attchement(issueIdOrKey, file_name):

 url = JIRA_URL + '/rest/api/2/issue/' + issueIdOrKey + "/attachments"

 auth = HTTPBasicAuth(JIRA_USERNAME, JIRA_PASSWORD)

 headers = {
    "Accept": "application/json",
    "X-Atlassian-Token": "no-check"
 }

 response = requests.request(
    "POST",
    url,
    headers = headers,
    auth = auth,
    files = {
         "file": (file_name, open(file_name,"rb"), "application-type")
    }
 )

 print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

def assign_issue(issue_id , assignee_id):
    url = JIRA_URL + "/rest/api/3/issue/" + issue_id + "/assignee"
    payload = json.dumps(
        {
            "accountId": assignee_id  
        }
        
    )
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.put(url, headers=headers, data=payload, auth=(JIRA_USERNAME, JIRA_PASSWORD))
    print(response)
    
def get_user(repo_name):
    print(repo_name)
    repo_name = repo_name.replace('.txt', '')
    repo_name = repo_name.replace('git-', '')
    repo_name= (repo_name).split('/')[-1]
    # repo_name = repo_name.replace('.txt', '')
    # repo_name = repo_name.replace('git-', '')
    with io.open("assign_user.csv", "r", encoding="utf-8") as f1:
        data = f1.read()
        f1.close()

    data = data.split("\n")

    for row in data:
        repo = row.split(",")[0]
        if repo == repo_name :
            print(row.split(","))
            return row.split(",")[1]
        

def  create_attach_jira():

    files = glob.glob('/home/ubuntu/truffelhog_automation/truffel_output_final/*.txt')
    for f in files:
        

        try:
            json_response = jira_rest_call(generate_issue_data(generate_summary(f), generate_description("")))
            issue_key = json_response['key']
            print("Created issue", issue_key)
            add_attchement(issue_key,f)
            assign_issue(issue_key, get_user(f) ) 
        except Exception as e:
            print(f"An error occurred: {e}")

def txt_formatter():
    files = glob.glob('/home/ubuntu/truffelhog_automation/truffel_output/*.txt')
    counter = 0
    total = len(files)

    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        if len(lines) <= 6: 
            #print(f'Skipping file {f} ... ({counter}/{total})')
            counter += 1
            continue
        
        counter += 1
        #print(f'Processing file {f}... ({counter}/{len(files)})')
        
        cleaned_data = []
        detector_type_found = False 
        
        for line in lines:
            # Skip the line if it starts with a numeric value
            if line.strip().startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                #print(f'Skipping line in file {f}: {line.strip()}')
                continue
            
            cells = line.strip().split('\t')
            cleaned_row = []
            
            for cell in cells:
                cell = demoji.replace(cell.strip())
                cell = re.sub(r'[^\w:/, .-;$#^&!@%^*()_+=]', '', cell)
                cell = re.sub(r'^0m', '', cell) 
                cell = re.sub(r'^1;92m', '', cell) 
                cell = re.sub(r'^92m|', '', cell)
                cell = re.sub(r'^33m', '', cell)
                cell = re.sub(r'\[33m|\[0m\[92m|\[37m', '', cell)  # Remove other color codes
                
                if "Detector Type" in cell:
                    detector_type_found = True
                    
                cleaned_row.append(cell)
            
            cleaned_data.append('\t'.join(cleaned_row))
        
        # Save the cleaned data to a text file only if "Detector Type" is found
        if detector_type_found:
            output_file = f
            output_path = '/home/ubuntu/truffelhog_automation/truffel_output_final/' + output_file.split('/')[-1]
            
            with open(output_path, 'w') as output_file:
                output_file.write('\n'.join(cleaned_data))
            
            #print(f'Processed file {f}, cleaned data saved to {output_path}')
        #else:
            #print(f'Detector Type not found in file {f}. No output file generated.')

txt_formatter()
create_attach_jira()
