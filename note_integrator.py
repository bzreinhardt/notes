import requests
import argparse
import os
import re

BASE_URL = "https://www.streak.com/api/"
BASE_HEADERS = {
    'content-type': "application/json",
    'authorization': "Basic YWE3NDRhMmQ5N2ZlNGZmMmI1YzFiMzFlNjZlNWE1NGY6"
    }
DEFAULT_TEAM = "Benjamin R's Team"

#for ref - streak api https://streak.readme.io/reference#list-all-boxes-in-pipeline

def get_team_key(team_name=DEFAULT_TEAM):
    url = BASE_URL+"v2/users/me/teams"
    response = requests.request("GET", url, headers=BASE_HEADERS)
    key = None
    for team in response.json()['results']:
        if team['name'] == team_name:
            key = team['key']
            break
    return key

def get_pipeline_list():
    url = BASE_URL+"v1/pipelines"
    response = requests.request("GET", url, headers=BASE_HEADERS)
    return response.json()

def get_pipeline_names():
    pipeline_list = get_pipeline_list()
    names = [pipe['name'] for pipe in pipeline_list]
    return names


def get_pipeline_key(pipeline_name):
    url = BASE_URL+"v1/pipelines"
    #agxzfm1haWxmb29nYWVyPAsSDE9yZ2FuaXphdGlvbiIVYnpyZWluaGFyZHRAZ21haWwuY29tDAsSCFdvcmtmbG93GICAssDJiuEJDA
    response = requests.request("GET", url, headers=BASE_HEADERS)
    for pipeline in response.json():
        if pipeline["name"] == pipeline_name:
            return pipeline["pipelineKey"]

def get_box_list(pipeline_key):
    url = BASE_URL+"v1/pipelines/%s/boxes"%pipeline_key
    response = requests.request("GET", url, headers=BASE_HEADERS)
    return response.json()

def check_box(pipeline_key, box_name):
    boxes = get_box_list(pipeline_key)
    box_out = None
    for box in boxes:
        if box['name'] == box_name:
            box_out = box
            break
    return key

def get_contact(contact_key):
    url = 'https://www.streak.com/api/v2/contacts/%s'%contact_key
    response = requests.request("GET", url, headers=BASE_HEADERS)
    return response.json()



def query(name_or_email):
    url = BASE_URL+"v1/search"
    querystring = {"query":name_or_email}
    response = requests.request("GET", url, headers=BASE_HEADERS, params=querystring)
    if 'results' not in response.json():
        print("did not get results for query %s"%name_or_email)
        print("response was")
        print(response.json())
        return {'orgs':[], 'contacts':[], 'boxes':[]}
    return response.json()['results']

def get_tags(content):
    pattern1 = r'(?<!\S)\#([.\w\/\-]+)[ \n]?(?!([\/ \w]+\w[#]))'
    pattern2 = r'(?<![\S])\#([^ \d][.\w\/ ]+?)\#([ \n]|$)'
    tags = []
    for matches in re.findall(pattern1, content):
        tag = matches[0]
        if "/" in tag:
            tags = tags + tag.split("/")
        else:
            tags.append(tag)
    for matches2 in re.findall(pattern2, content):
        tag2 = matches2[0]
        if "/" in tag2:
            tags = tags + tag2.split("/")
        else:
            tags.append(tag2)
    return tags

def construct_payload(parameters):
    payload = []
    for param in parameters:
        if type(parameters[param]) != type([]) and len(parameters[param]) > 0:
            #print(type(param))
            #print(type(parameters[param]))
            payload.append("\"%s\":\"%s\""%(param, parameters[param]))
        elif len(parameters[param]) > 0:
            all = []
            string = "\"%s\":["%param
            for item in parameters[param]:
                all.append("\"%s\""%item)
            string = "\"%s\":["%param + ",".join(all) + "]"
            payload.append(string)
    return "{" + ",".join(payload) + "}"


def create_contact(team_id, parameters={}, emails=None):
    url = BASE_URL+ "v2/teams/%s/contacts/"%team_id
    querystring = {"getIfExisting":"false"}
    payload = construct_payload(parameters)
    headers = BASE_HEADERS
    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    return response.json()

def update_contact(contact_key, parameters={}):
    url = 'https://www.streak.com/api/v2/contacts/%s'%contact_key
    data = construct_payload(parameters)
    response = requests.request("POST", url, data=data, headers=BASE_HEADERS)
    return response.json()


def create_org(org_name):
    team_key = get_team_key()
    url = 'https://www.streak.com/api/v2/teams/%s/organizations'%team_key
    #--data '{"domains":["NASA",null]}'
    payload='{"name":"%s"}'%org_name
    response = requests.request("POST", url, data=payload, headers=BASE_HEADERS)
    if 'key' in response.json():
        return response.json()['key']
    else:
        return None

def check_org(org_name):
    response = query(org_name)
    if len(response['orgs']) > 0:
        for org in response['orgs']:
            if 'name' in org:
                if org['name'].lower() == org_name.lower():
                    return org['key']
    return None


def create_box(pipeline_id, parameters):
    url = BASE_URL+ "v2/pipelines/%s/boxes"%pipeline_id
    payload = construct_payload(parameters)
    #payload = "{\"name\":\"%s\",\"notes\":\"%s\"}"%(name,notes)
    response = requests.request("POST", url, data=payload, headers=BASE_HEADERS)
    return response.json()

def get_box(box_id):
    url = BASE_URL+"/v1/boxes/%s"%box_id
    response = requests.request("GET", url, headers=BASE_HEADERS)
    return response.json()

def add_contact_to_box(box_key, contact_key):
    url = "https://www.streak.com/api/v1/boxes/"+box_key
    payload = "{\"contacts\":[{\"isStarred\":false,\"key\":\"%s\"}]}"%contact_key
    response = requests.request("POST", url, data=payload, headers=BASE_HEADERS)
    return response.json()

def add_org_to_box(box_key, org_key):
    url = "https://www.streak.com/api/v1/boxes/"+box_key
    payload = "{\"organizations\":[{\"isStarred\":false,\"key\":\"%s\"}]}"%org_key
    response = requests.request("POST", url, data=payload, headers=BASE_HEADERS)
    return response.json()

def update_box(box_key, parameters):
    url = "https://www.streak.com/api/v1/boxes/"+box_key
    payload = construct_payload(parameters)
    response = requests.request("POST", url, data=payload, headers=BASE_HEADERS)
    return response.json()


def process_note_contact(structured_note, pipeline_name="Parpa Research", update=False):
    if 'person' not in structured_note['tags']:
        print("Note not for person")
        return 1
    name = structured_note['title']
    box_parameters = {"name":name}
    parameters = {"emailAddresses":[], "phoneNumbers":[], "addresses":[], "other":''}
    org_parameters = {'name':''}
    url = None
    if len(name.split(' ')) < 2:
        print("need first and last name for %s"%name)
        return 1
    parameters['givenName'] = name.split(' ')[0]
    parameters['familyName'] = ' '.join(name.split(' ')[1:])
    for value in structured_note['values']:
        val = value["val"]
        type = value['type']
        if type.lower() == "email":
            parameters['emailAddresses'].append(val)
        if type.lower() == 'phone':
            parameters['phoneNumbers'].append(val)
        if type.lower() == "linkedin":
            parameters['linkedinHandle'] = val
        if type.lower() == "twitter":
            parameters['twitterHandle'] = val
        if type.lower() == "photo":
            parameters['photoUrl'] = val
        if type.lower() == "facebook":
            parameters['facebookHandle'] = val
        if type.lower() == "givenName":
            parameters['givenName'] = val
        if type.lower() == "familyName":
            parameters['familyName'] = val
        if type.lower() == "website":
            parameters['other']+="Website:%s "%val
        if type.lower() == "nickname":
            parameters['other']+="Nickname:%s "%val
        if type.lower() == "loc":
            parameters['addresses'].append(val)
        if type.lower() == "url":
            box_parameters['notes'] = val
        if type.lower().startswith("org"):
            org_parameters['name'] = val

    box_created = False
    contact_created = False
    pipeline_id = get_pipeline_key(pipeline_name)

    #check if there's a box for the person
    results = query(name)
    if len(results['boxes']) == 0:
        #create a box for the person
        box = create_box(pipeline_id, box_parameters)
        box_created = True
        print("created box for %s"%name)
        #aagxzfm1haWxmb29nYWVyOAsSDE9yZ2FuaXphdGlvbiIVYnpyZWluaGFyZHRAZ21haWwuY29tDAsSBENhc2UYgICy8JDixgkM
    else:
        box = results['boxes'][0]
        if update:
            response = update_box(box['boxKey'], box_parameters)

    if len(results['contacts']) == 0:
        team_id = get_team_key()
        response = create_contact(team_id, parameters=parameters)
        contact = response
        #VGVhbUNvbnRhY3Qsfn5zdHJlYWtsb25naWR-fjU5MDU2NjQwMTk1NjI0OTY
        contact_created = True
    else:
        contact = get_contact(results['contacts'][0]['key'])
    contact_response = add_contact_to_box(box['boxKey'],contact['key'])
    if (org_parameters['name']):
        org_key = check_org(org_parameters['name'])
        if not org_key:
            org_key = create_org(org_parameters['name'])
        org_response = add_org_to_box(box['boxKey'], org_key)
    return box, contact


def get_web_url(content):
    matches = re.findall(r'(?<=Web URL for this note]\().*', content)
    url = None
    if len(matches) > 0:
        url = matches[0].split(")")[0:-1]
    if type(url) == type([]):
        url = url[0]
    return url


def note_to_structure(path):
    note = {'title':'Untitled', 'values':[], 'sections':{'none':{'content':[]}}, 'tags':[]}
    if not path.endswith(".md"):
        return note
    with open(path, 'r') as f:
        content = f.read()
    current_heading = 'none'
    for line in content.split('\n'):
        if len(line) < 2:
            continue
        if line[0] != "#":
            note['sections'][current_heading]['content'].append(line)
            if len(line.split(":")) > 1:
                type = line.split(":")[0]
                val = ":".join(line.split(":")[1:]).strip()
                if len(val.strip()) > 0:
                    note['values'].append({'type':type,'val':val})
            continue
        #deal with headers and tags
        if line[1] == " ":
            note['title'] = line.replace('#','').strip()
        elif line[1] != '#':
            #ignore tags
            continue
        elif line[1]:
            current_heading = line.replace('#','')
            note['sections'][current_heading] = {'content':[]}
    if note['title'] == 'Untitled':
        note['title'] = os.path.basename(path)[0:-3]
    note['tags'] = get_tags(content)
    note['values'].append({'type':'url','val':get_web_url(content)})
    #Strip leading and ending brackets
    for i, value in enumerate(note['values']):
        if not value['val']:
            continue
        if value['val'].startswith('[') and value['val'].endswith(']'):
            if value['val'].startswith('[[') and value['val'].endswith(']]'):
                note['values'][i] = {'type':value['type'], 'val':value['val'][2:-2], 'meta':'internal link'}
            else:
                note['values'][i] = {'type':value['type'], 'val':value['val'][1:-1], 'meta':'external link'}
    return note

def single_note(path, pipeline_names, pipeline_tags, update=False):
    structured_note = note_to_structure(path)
    create_contact = False
    pipeline = None
    #check for pipeline value
    pipeline = next((x for x in structured_note['values'] if x['type'] == 'Pipeline'), None)
    #check for pipeline tag
    if set(structured_note['tags']) & set(pipeline_tags):
        #this complex line just grabs the pipeline name that corresponds to the tag that's present
        pipeline = pipeline_names[pipeline_tags.index(list(set(structured_note['tags']) & set(pipeline_tags))[0])]
    if pipeline is not None:
        process_note_contact(structured_note, pipeline_name=pipeline, update=update)


def main(directory, update=False):
    files = os.listdir(directory)
    pipeline_names = get_pipeline_names()
    pipeline_tags = [name.lower().replace(" ","-") for name in pipeline_names]
    for file in files:
        path = os.path.join(directory, file)
        structured_note = note_to_structure(path)
        create_contact = False
        pipeline = None
        #check for pipeline value
        pipeline = next((x for x in structured_note['values'] if x['type'] == 'Pipeline'), None)
        #check for pipeline tag
        if set(structured_note['tags']) & set(pipeline_tags):
            #this complex line just grabs the pipeline name that corresponds to the tag that's present
            pipeline = pipeline_names[pipeline_tags.index(list(set(structured_note['tags']) & set(pipeline_tags))[0])]
        if pipeline is not None:
            process_note_contact(structured_note, pipeline_name=pipeline, update=update)

def test(path):
    pipeline_names = get_pipeline_names()




if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--note')
    parser.add_argument('--pipe')
    parser.add_argument('--box')
    parser.add_argument('--team', action='store_true')
    parser.add_argument('--query')
    parser.add_argument('--test')
    parser.add_argument('--dir')
    parser.add_argument('--update', action='store_true')
    parsed_args = vars(parser.parse_args())
    update = parsed_args.get('update')
    if parsed_args.get("note"):
        path = os.path.abspath(parsed_args.get("note"))
        pipeline_names = get_pipeline_names()
        pipeline_tags = [name.lower().replace(" ","-") for name in pipeline_names]
        single_note(path, pipeline_names, pipeline_tags, update)
    elif parsed_args.get("pipe"):
        key = get_pipeline_key(parsed_args.get("pipe"))
        if parsed_args.get("box"):
            box = check_box(key, parsed_args.get("box"))
            print(box)
        else:
            boxes = get_box_list(key)
            print(key)
    elif parsed_args.get("team"):
        print(get_team_key(DEFAULT_TEAM))
    elif parsed_args.get("query"):
        print(query(parsed_args.get("query")))
    elif parsed_args.get("dir"):
        main(parsed_args.get("dir"))
    elif parsed_args.get("test"):
        test(parsed_args.get('test'))
