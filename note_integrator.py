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

def get_team_key(team_name):
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
    print(response.text)
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

def query(name_or_email):
    url = BASE_URL+"v1/search"
    querystring = {"query":name_or_email}
    response = requests.request("GET", url, headers=BASE_HEADERS, params=querystring)
    return response.json()['results']

def get_tags(content):
    pattern1 = r'(?<!\S)\#([.\w\/\-]+)[ \n]?(?!([\/ \w]+\w[#]))'
    pattern2 = r'(?<![\S])\#([^ \d][.\w\/ ]+?)\#([ \n]|$)'
    tags = []
    for matches in re.findall(pattern1, content):
        tag = matches[0]
        tags.append(tag)
    for matches2 in re.findall(pattern2, content):
        tag2 = matches2[0]
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
    print("Payload:")
    print(payload)
    headers = BASE_HEADERS
    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    print(response.text)
    return response.json()

def create_box(pipeline_id, name):
    url = BASE_URL+ "v2/pipelines/%s/boxes"%pipeline_id
    payload = "{\"name\":\"%s\"}"%name
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


def process_note_contact(structured_note, pipeline_name="Parpa Research"):
    if 'person' not in structured_note['tags']:
        print("Note not for person")
        return 1
    parameters = {"emailAddresses":[], "phoneNumbers":[], "addresses":[], "other":''}
    name = structured_note['title']
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
    #check if there's a box for the person
    results = query(name)
    box_created = False
    contact_created = False
    pipeline_id = get_pipeline_key(pipeline_name)
    if len(results['boxes']) == 0:
        #create a box for the person
        box = create_box(pipeline_id, name)
        box_created = True
        print("created box for %s"%name)
        #aagxzfm1haWxmb29nYWVyOAsSDE9yZ2FuaXphdGlvbiIVYnpyZWluaGFyZHRAZ21haWwuY29tDAsSBENhc2UYgICy8JDixgkM
    else:
        box = results['boxes'][0]
    if len(results['contacts']) == 0:
        team_id = get_team_key(DEFAULT_TEAM)
        response = create_contact(team_id, parameters=parameters)
        contact = response
        #VGVhbUNvbnRhY3Qsfn5zdHJlYWtsb25naWR-fjU5MDU2NjQwMTk1NjI0OTY
        contact_created = True
        print("created contact for %s"%name)
    else:
        contact = results['contacts'][0]
    contact_response = add_contact_to_box(box['boxKey'],contact['key'])

    return box, contact


def note_to_structure(content):
    note = {'title':'Untitled', 'values':[], 'sections':{'none':{'content':[]}}, 'tags':[]}
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
    note['tags'] = get_tags(content)
    return note

def main(directory):
    files = os.listdir(directory)
    pipeline_names = get_pipeline_names()
    pipeline_tags = [name.lower().replace(" ","-") for name in pipeline_names]
    for file in files:
        if not file.endswith(".md"):
            continue
        path = os.path.join(directory, file)
        with open (path, 'r') as f:
            content = f.read()
        structured_note = note_to_structure(content)
        create_contact = False
        pipeline = None
        #check for pipeline value
        pipeline = next((x for x in structured_note['values'] if x['type'] == 'Pipeline'), None)
        #check for pipeline tag
        if set(structured_note['tags']) & set(pipeline_tags):
            #this complex line just grabs the pipeline name that corresponds to the tag that's present
            pipeline = pipeline_names[pipeline_tags.index(list(set(structured_note['tags']) & set(pipeline_tags))[0])]
        if pipeline is not None:
            process_note_contact(structured_note, pipeline_name=pipeline)

def test_note_to_pipeline(content):
    structured_note = note_to_structure(content)
    box, contact = process_note_contact(structured_note)
    print("Box")
    print(box)
    print("CONTACT")
    print(contact)



if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--note')
    parser.add_argument('--pipe')
    parser.add_argument('--box')
    parser.add_argument('--team', action='store_true')
    parser.add_argument('--query')
    parser.add_argument('--test')
    parser.add_argument('--dir')
    parsed_args = vars(parser.parse_args())
    if parsed_args.get("note"):
        path = os.path.abspath(parsed_args.get("note"))
        with open(path, 'r') as f:
            content = f.read()
        note = note_to_structure(content)
        print(note)
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
    elif parsed_args.get("test"):
        path = os.path.abspath(parsed_args.get("test"))
        with open(path, 'r') as f:
            content = f.read()
        test_note_to_pipeline(content)
    elif parsed_args.get("dir"):
        main(parsed_args.get("dir"))
