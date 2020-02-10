import argparse
import os

def remove_contact_info(content):
    lines = content.split("\n")
    lines_out = []
    for line in lines:
        if not (line.lower().startswith("email:") or line.lower().startswith("phone:") or line.lower().startswith("contacted")):
            lines_out.append(line)
    return "\n".join(lines_out)

def make_note_publishable(path):
    with open(path, 'r') as f:
        content = f.read()
    content_out = remove_contact_info(content)
    if content_out != content:
        with open(path, 'w') as f:
            f.write(content_out)

def main(directory):
    files = os.listdir(directory)
    for file in files:
        if not file.endswith(".md"):
            continue
        path = os.path.join(directory, file)
        make_note_publishable(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir')
    parsed_args = vars(parser.parse_args())
    directory = os.path.abspath(parsed_args.get("dir"))
    main(directory)
