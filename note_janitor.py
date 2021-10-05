import argparse
import os
import re
import json
import requests
from subprocess import Popen, PIPE

BASE_URL = "http://notes.benjaminreinhardt.com"
JSON_BIN = "https://api.jsonbin.io/b/5e5ca0e4e68645052627e710"



def get_creation_and_modification(path):
    created = datetime.fromtimestamp(os.stat(path).st_birthtime)
    modified = datetime.fromtimestamp(os.path.getmtime(path))

def clean_title(title):
    title = title[:256].strip()
    if title == "":
        title = "Untitled"
    title = re.sub(r'[/\\*?$@!^&\|~:\.%]', r'-', title)
    title = re.sub(r'-$', r'', title)
    return title.strip()


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


def get_title(content):
    lines = content.split("\n")
    title = lines[0]
    if len(title) == 0:
        print("no title for note with second line %s"%lines[1])
        return None
    if title[0] == '#':
        title = title[1:].strip()
    else:
        title = None
        print("no title for note with second line %s"%lines[1])
    return title

def get_note_url(content):
    title = get_title(content)
    if not title:
        return None
    clean_note_title = clean_title(title)
    url = BASE_URL + "/" + clean_note_title.replace(" ","_")
    if url.endswith(")"):
        url = url + " "
    return url


def add_web_url(content):
    url = get_note_url(content)

    if content.find("Web URL for this note") > -1:
        content_out = re.sub(r'\[Web URL for this note]\((.*?)\n', "[Web URL for this note](%s)\n"%url, content)
    else:
        backlink_index = content.find('## Backlinks')
        note_id_index = content.find('<!-- {Bear')
        if backlink_index > -1:
            content_out = content[0:backlink_index] + "[Web URL for this note](%s)\n\n"%url + content[backlink_index:]
        else:
            content_out = content[0:note_id_index] + "[Web URL for this note](%s)\n\n"%url + content[note_id_index:]
    return content_out

def add_annotate_url(content):
    annotate_url = "http://via.hypothes.is/" + get_note_url(content)
    if content.find("Comment on this note") > -1:
        content_out = re.sub(r'\[Comment on this note]\((.*?)\n', "[Comment on this note](%s)\n"%annotate_url, content)
    else:
        backlink_index = content.find('## Backlinks')
        note_id_index = content.find('<!-- {Bear')
        if backlink_index > -1:
            content_out = content[0:backlink_index] + "\n[Comment on this note](%s)\n\n"%annotate_url + content[backlink_index:]
        else:
            content_out = content[0:note_id_index] + "\n[Comment on this note](%s)\n\n"%annotate_url + content[note_id_index:]
    return content_out

def remove_urls(content):
    content = re.sub(r'\[Comment on this note]\((.*?)\n', "", content)
    content = re.sub(r'\[Web URL for this note]\((.*?)\n', "", content)
    return content


def hide_tags(md_text):
    # Hide tags from being seen as H1, by placing `period+space` at start of line:
    md_text =  re.sub(r'(\n)[ \t]*(\#[^\s#].*)', r'\1<!-- \2 -->', md_text)
    return md_text

def remove_comments(md_text):
    md_text = re.sub(r'<!--(.*?)-->','', md_text)
    return md_text


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
    if len(title) == 0 or title[0] != '#':
        return content
    duplicated_title = False

    for i, line in enumerate(lines):
        if i != 0 and line != title:
            new_lines.append(line)
        if i != 0 and line == title:
            print("found duplicated line")
            duplicated_title = True
            continue
    if not duplicated_title:
        new_lines = [title] + new_lines

    content_out = '\n'.join(new_lines)
    return content_out

def grab_todo(content):
    lines = content.split("\n")
    title = get_title(content)
    lines_out = []
    for line in lines:

        if line.lower().find("todo:") > -1:
            if len(line.lower().split("todo:")) > 1:
                todo = line.lower().split("todo:")[1]
                todo = todo + " from Bear Note %s"%title
                ##tag1 #tag2 name [project/area] ::note >duedate
                script = 'tell application "Things3.app"\n\
                            set newToDo to make new to do with properties {name:"%s"}\n\
                          end tell\n'%todo
                p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                stdout, stderr = p.communicate(script)
        else:
            lines_out.append(line)
    return "\n".join(lines_out)


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
    content_out = add_web_url(content)
    content_out = add_annotate_url(content_out)
    content_out = remove_excessive_newlines(content_out)
    content_out = grab_todo(content_out)
    content_out = remove_titles(content_out)
    if no_backlinks:
        content_out = remove_backlinks(content_out)
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
    parser.add_argument('--note', action="store_true")
    parser.add_argument('--rl', action="store_true")
    parser.add_argument('--upload', action="store_true")
    parsed_args = vars(parser.parse_args())
    directory = os.path.abspath(parsed_args.get("dir"))
    if parsed_args.get("pub"):
        make_dir_publishable(directory)
    if parsed_args.get("note"):
        process_note(directory, no_backlinks=parsed_args.get("rl"))
    else:
        main(directory, no_backlinks=parsed_args.get("rl"), upload_links=parsed_args.get("upload"))
