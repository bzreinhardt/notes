import argparse
import os
import re

BASE_URL = "https://notes.benjaminreinhardt.com"

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


def add_web_url(baseurl, path, content):
    url = baseurl + "/" + os.path.basename(path)[:-3].replace(" ","_")
    # This line just makes sure there's only one URL per note
    content = re.sub(r'\[Web URL for this note]\((.*?)\n', '', content)
    backlink_index = content.find('## Backlinks')
    note_id_index = content.find('<!-- {Bear')
    if backlink_index > -1:
        content_out = content[0:backlink_index] + "\n[Web URL for this note](%s)\n\n"%url + content[backlink_index:]
    else:
        content_out = content[0:note_id_index] + "\n[Web URL for this note](%s)\n\n"%url + content[note_id_index:]
    return content_out

def remove_extra_titles(content):
    lines = content.split("\n")
    new_lines = []
    title = lines[0]
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

def process_note(path, no_backlinks=False):
    with open(path, 'r') as f:
        content = f.read()
    content_out = add_web_url(BASE_URL, path, content)
    content_out = remove_extra_titles(content_out)
    content_out = remove_excessive_newlines(content_out)
    if no_backlinks:
        content_out = remove_backlinks(content_out)
    if content_out != content:
        with open(path, 'w') as f:
            f.write(content_out)


def main(directory, no_backlinks=False):
    files = os.listdir(directory)
    for file in files:
        if not file.endswith(".md"):
            continue
        path = os.path.join(directory, file)
        process_note(path, no_backlinks=no_backlinks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir')
    parser.add_argument('--pub', action="store_true")
    parser.add_argument('--note')
    parser.add_argument('--rl', action="store_true")
    parsed_args = vars(parser.parse_args())
    directory = os.path.abspath(parsed_args.get("dir"))
    if parsed_args.get("pub"):
        make_dir_publishable(directory)
    if parsed_args.get("note"):
        path = os.path.abspath(parsed_args.get("note"))
        process_note(path, no_backlinks=parsed_args.get("rl"))
    else:
        main(directory, no_backlinks=parsed_args.get("rl"))
