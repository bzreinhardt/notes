import argparse
import os


def fix_metadata(content):
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if len(line) > 0 and line[0] =="|":
            new_line = ""
            field = line[1:].split("|")[0].strip()
            value = line[1:].split("|")[1].strip()
            if field == "Authors":
                values = value.split(" ")
                new_values = []
                for value in values:
                    if value[-1] == ".":
                        print(value)
                        continue
                    else:
                        new_values.append(value)
                print(new_values)
                value = " ".join(new_values)
                new_line = "-  " + field + " : " + value
            elif field == "Date":
                value = value.replace("[[","").replace("]]","")
                year = value.split("/")[-1]
                value = "[["+year+"]]"
                new_line = "-  " + field + " : " + value
            elif field == "Cite key":
                cite_key = value[1:-1]
                new_line = "-  " + field + " : " + value
            elif field == "PDF Attachments":
                value = value.split("(")[0]+"("+"file:///Users/zaaron/Dropbox/Cross Device Reference/Papers/"+cite_key+".pdf)"
                new_line = "-  " + field + " : " + value
            else:
                new_line = "- "+line[1:].replace("|",":")
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)

def downgrade_headers(content):
    lines = content.split("\n")
    new_lines = [lines[0]]
    for i, line in enumerate(lines[1:]):
        if line[0:2] == "# ":
            new_lines.append("#"+line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)



def rename_to_citekey(content, path):
    lines = content.split("\n")
    title = os.path.basename(path).split(".")[0]
    if title not in lines[0]:
        lines = ["# "+title]+lines[2:]
    return "\n".join(lines)

def process_note(path):
    with open(path, 'r') as f:
        content = f.read()
    content_out = downgrade_headers(content)
    content_out = rename_to_citekey(content_out, path)
    content_out = fix_metadata(content_out)
    if content_out != content:
        with open(path, 'w') as f:
            f.write(content_out)

def main(directory):
    files = os.listdir(directory)
    for file in files:
        if not file.endswith(".md"):
            continue
        path = os.path.join(directory, file)
        process_note(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir')
    parser.add_argument('--note', action="store_true")
    parsed_args = vars(parser.parse_args())
    directory = os.path.abspath(parsed_args.get("dir"))
    if parsed_args.get("note"):
        process_note(directory)
    else:
        main(directory)
