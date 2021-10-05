import networkx as nx
from note_janitor import get_links, get_title, get_body, remove_backlinks, remove_urls
import argparse
import os
import re


def add_note_to_graph(graph, note_content):
    title = get_title(note_content)
    if title == None:
        print("Warning: no note title")
        return graph, title
    if not graph.has_node(title):
        graph.add_node(title)
    links = get_links(note_content, title)
    for link in links:
        #source is all going to be this note
        if not graph.has_node(link['target']):
            graph.add_node(link['target'])
        graph.add_edge(link['source'], link['target'])
    return graph, title

def create_outline_from_note(graph,
                             note_title,
                             link_note=True,
                             body_path_dict=None,
                             added_notes={},
                             current_depth=0,
                             max_depth=2,
                             ignore_repeated_notes=True):
    """
    Creates an outline from notes
    """
    # Check whether note has already been added to outline
    if note_title in added_notes:
        added_notes[note_title].append(current_depth)
        if ignore_repeated_notes:
            return None, added_notes
        else:
            if link_note:
                title = "[[%s]]"%note_title
            else:
                title = note_title
            return "- "+title+'**', added_notes
    added_notes[note_title]=[current_depth]
    neighbors = nx.neighbors(graph, note_title)
    title = note_title
    if link_note:
        title = "[[%s]]"%note_title
    if body_path_dict and note_title in body_path_dict:
        with open(body_path_dict[note_title]['path'], 'r') as f:
            content = f.read()
        body = get_body(content)
        title += "\n%s"%body
    if current_depth < max_depth:
        outline = "- %s"%title
        for neighbor in neighbors:
            neighbor_outline, added_notes = create_outline_from_note(graph,
                                                neighbor,
                                                link_note=link_note,
                                                body_path_dict=body_path_dict,
                                                added_notes=added_notes,
                                                current_depth=current_depth+1,
                                                max_depth=max_depth,
                                                ignore_repeated_notes=ignore_repeated_notes)
            if neighbor_outline is None:
                continue
            neighbor_outline_lines = neighbor_outline.split("\n")
            for line in neighbor_outline_lines:
                outline += "\n\t%s"%line
    else:
        outline = "- %s"%title
    return outline, added_notes

def expand_note(root_note, depth=1, out_file=None):
    directory = os.path.dirname(root_note)
    graph, extra_info = create_graph_from_dir(directory)
    with open(root_note) as f:
        content = f.read()
    content = remove_backlinks(content)
    lines = content.split("\n")
    refs = re.finditer('\[\[.*?\]\]', content)
    cursor = 0
    out = ''
    for ref in refs:
        out += content[cursor:ref.start()]
        # get content for ref and add to out
        title = content[ref.start():ref.end()].strip('[[').strip(']]')
        path = extra_info[title]['path']
        with open(path, 'r') as f:
            sub_content = f.read()
        sub_body = remove_urls(remove_backlinks(get_body(sub_content)))
        if out[-2] == '-':
            out = out[0:-2]
        out += '## '+title +'\n'
        out += sub_body
        cursor = ref.end()
    out += content[cursor:]
    if out_file:
        with open(out_file, 'w') as f:
            f.write(out)
    return out


def create_graph_from_dir(directory):
    files = os.listdir(directory)
    graph = nx.DiGraph()
    extra_info = {}
    for file in files:
        if not file.endswith(".md"):
            continue
        path = os.path.join(directory, file)
        with open(path, 'r') as f:
            content = f.read()
        graph, title = add_note_to_graph(graph, content)
        if title:
            extra_info[title] = {'path':path}
    return graph, extra_info

def get_note_bodies(directory):
    bodies = {}
    files = os.listdir(directory)
    for file in files:
        if not file.endswith(".md"):
            continue
        path = os.path.join(directory, file)
        with open(path, 'r') as f:
            content = f.read()
        title = get_title(content)
        body = get_body(content)
        bodies[title] = body
    return bodies



def main(root_note, get_bodies=False, link_note=True, outfile=None, depth=1, ignore_repeated_notes=True):
    directory = os.path.dirname(root_note)
    with open(root_note) as f:
        root_title = get_title(f.read())
    graph, extra_info = create_graph_from_dir(directory)
    if get_bodies:
        outline, added_notes = create_outline_from_note(graph, root_title, body_path_dict=extra_info, link_note=link_note, max_depth=depth, ignore_repeated_notes=ignore_repeated_notes)
    else:
        outline, added_notes = create_outline_from_note(graph, root_title, link_note=link_note, max_depth=depth, ignore_repeated_notes=ignore_repeated_notes)
    if not outfile:
        out_file = os.path.join(directory, os.path.basename(root_note)[0:-3] + " outline.md")
    else:
        out_file = outfile
    notelist_file = out_file[:-3] + "_note_list.md"
    out_content = "# " + root_note + " outline\n" + outline
    with open(out_file, 'w') as f:
        f.write(out_content)
    with open(notelist_file, 'w') as f:
        for note in added_notes:
            note_name = note
            if link_note:
                note_name = "[[%s]]"%note
            f.write('- %s appears %d times\n'%(note_name, len(added_notes[note])))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('root')
    parser.add_argument('--expand', action="store_true")
    parser.add_argument('--bodies', action="store_true")
    parser.add_argument('--nolinks', action="store_false")
    parser.add_argument('--outfile', default=None)
    parser.add_argument('--depth', type=int, default=2)
    parser.add_argument('--mark_repeats', action="store_false")
    parsed_args = vars(parser.parse_args())
    depth = parsed_args.get("depth")
    directory = os.path.abspath(parsed_args.get("root"))
    out_file = parsed_args.get("outfile")
    root_note = parsed_args.get("root")
    if not out_file:
        out_file = os.path.join(directory, os.path.basename(root_note)[0:-3] + " outline.md")
    if parsed_args.get("expand"):
        expand_note(parsed_args.get("root"), out_file=out_file)
    else:
        main(parsed_args.get("root"),
            get_bodies=parsed_args.get("bodies"),
            link_note=parsed_args.get("nolinks"),
            outfile=parsed_args.get("outfile"),
            depth=depth,
            ignore_repeated_notes=parsed_args.get("mark_repeats"))
