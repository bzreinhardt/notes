import argparse
import os
import re
import json
import requests

BASE_URL = "https://notes.benjaminreinhardt.com"
JSON_BIN = "https://api.jsonbin.io/b/5e5ca0e4e68645052627e710"



def get_creation_and_modification(path):
    created = datetime.fromtimestamp(os.stat(path).st_birthtime)
    modified = datetime.fromtimestamp(os.path.getmtime(path))




def remove_backlinks(content):
    backlink_index = content.find("## Backlinks")
    comment_index = content.find("<!-- ")
    content_out = content
    if backlink_index > -1:
        content_out = content[0:backlink_index]+content[comment_index:]
    return content_out

def remove_extra_tags(content):
    #assumes no more than one extra
    tags = re.finditer(r'<!-- #(.*?)-->\n', content)
    remove_indices = []
    for i, tag in enumerate(tags):
        if i != 0:
            remove_indices += [tag.span()[0], tag.span()[1]]
    if len(remove_indices) == 0:
        return content
    if len(remove_indices) == 2:
        return content[0:remove_indices[0]] + content[remove_indices[1]:]
    if len(remove_indices) > 2:
        print("ERR: more than one extra tag for %s"%content)
        return content


def get_note_url(baseurl, clean_note_title):
    return baseurl + "/" + clean_note_title.replace(" ","_")


def add_web_url(baseurl, path, content):
    url = get_note_url(baseurl, os.path.basename(path)[:-3])
    # This line just makes sure there's only one URL per note
    content = re.sub(r'\[Web URL for this note]\((.*?)\n', '', content)
    backlink_index = content.find('## Backlinks')
    note_id_index = content.find('<!-- {Bear')
    if backlink_index > -1:
        content_out = content[0:backlink_index] + "\n[Web URL for this note](%s)\n\n"%url + content[backlink_index:]
    else:
        content_out = content[0:note_id_index] + "\n[Web URL for this note](%s)\n\n"%url + content[note_id_index:]
    return content_out

def add_annotate_url(baseurl, path, content):
    annotate_url = "https://via.hypothes.is/" + get_note_url(baseurl, os.path.basename(path)[:-3])
    content = re.sub(r'\[Comment on this note]\((.*?)\n', '', content)

    backlink_index = content.find('## Backlinks')
    note_id_index = content.find('<!-- {Bear')
    if backlink_index > -1:
        content_out = content[0:backlink_index] + "\n[Comment on this note](%s)\n\n"%annotate_url + content[backlink_index:]
    else:
        content_out = content[0:note_id_index] + "\n[Comment on this note](%s)\n\n"%annotate_url + content[note_id_index:]
    return content_out

def hide_tags(md_text):
    # Hide tags from being seen as H1, by placing `period+space` at start of line:
    md_text =  re.sub(r'(\n)[ \t]*(\#[^\s#].*)', r'\1<!-- \2 -->', md_text)
    return md_text

def remove_comments(md_text):
    md_text = re.sub(r'<!--(.*?)-->','', md_text)
    return md_text

def get_title(content):
    lines = content.split("\n")
    title = lines[0]
    if title[0] == '#':
        title = title[1:].strip()
    else:
        title = None
    return title

def get_body(content, ignore_backlinks=True, ignore_hashtags=True):
    content = content.split("## Backlinks")[0]
    content = hide_tags(content)
    content = remove_comments(content)
    lines = content.split("\n")
    body = "\n".join(lines[1:])
    return body


def remove_titles(content):
    lines = content.split("\n")
    title = lines[0]
    new_lines = []
    if len(title) == 0:
        return content
    if title[0] == '#':
        for i, line in enumerate(lines):
            if line != title:
                new_lines.append(line)
    content_out = '\n'.join(new_lines)
    return content_out


def remove_excessive_newlines(content):
    out = re.sub(r'(\ \n){2,}','\n\n', content)
    return re.sub(r'(\n){2,}','\n\n', out)

def get_links(content, title, ignore_backlinks=True):
    links = []
    if ignore_backlinks:
        content = content.split("## Backlinks")[0]
    lines = content.split("\n")
    refs = re.findall('\[\[.*?\]\]', content)
    refs = [l.strip('[[').strip(']]') for l in refs]
    for ref in refs:
        links.append({"source":title, "target":ref, "type":"link"})
    return links

def process_note(path, no_backlinks=False, return_links=False):
    with open(path, 'r') as f:
        content = f.read()
    content_out = add_web_url(BASE_URL, path, content)
    content_out = add_annotate_url(BASE_URL, path, content_out)
    content_out = remove_excessive_newlines(content_out)
    if no_backlinks:
        content_out = remove_backlinks(content_out)
    content_out = remove_titles(content_out)
    if content_out != content:
        with open(path, 'w') as f:
            f.write(content_out)
    if return_links:
        return get_links(content_out, os.path.basename(path)[:-3])
    else:
        return []


def get_orphans(links):
    nodes = {}
    orphans = []
    # Create Nodes
    for link in links:
        if link["source"] not in nodes:
            nodes[link["source"]] = {"to":[], "from":[]}
        if link["target"] not in nodes:
            nodes[link["target"]] = {"to":[], "from":[]}
        nodes[link["source"]]["to"].append(link["target"])
        nodes[link["target"]]["from"].append(link["source"])
    # Find Orphan Nodes
    for node in nodes:
        if len(nodes[node]["to"]) == 1 and len(nodes[node]["from"]) == 1:
            orphans.append(node)

def upload_graph(data):
    print("data length = %d"%len(data))
    print("offdending data:")
    print(data[3977])
    json_data = json.dumps([data])
    with open('json_links.json', 'w') as f:
        f.write(json_data)
    '''
    url = JSON_BIN
    payload = json_data
    headers = {
        'content-type': "application/json",
        'secret-key':os.environ['JSONBIN_KEY'],
    }
    response = requests.request("PUT", url, data=payload, headers=headers)
    return response.json()
    '''


def main(directory, no_backlinks=False, upload_links=False):
    files = os.listdir(directory)
    links = []
    for file in files:
        if not file.endswith(".md"):
            continue
        path = os.path.join(directory, file)
        links_out = process_note(path, no_backlinks=no_backlinks, return_links=upload_links)
        if upload_links:
            links = links + links_out
    if upload_links:
        upload_graph(links)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir')
    parser.add_argument('--pub', action="store_true")
    parser.add_argument('--note')
    parser.add_argument('--rl', action="store_true")
    parser.add_argument('--upload', action="store_true")
    parsed_args = vars(parser.parse_args())
    directory = os.path.abspath(parsed_args.get("dir"))
    if parsed_args.get("pub"):
        make_dir_publishable(directory)
    if parsed_args.get("note"):
        path = os.path.abspath(parsed_args.get("note"))
        process_note(path, no_backlinks=parsed_args.get("rl"))
    else:
        main(directory, no_backlinks=parsed_args.get("rl"), upload_links=parsed_args.get("upload"))
