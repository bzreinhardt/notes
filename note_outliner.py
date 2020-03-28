import networkx as nx
from note_janitor import get_links, get_title, get_body
import argparse
import os


def add_note_to_graph(graph, note_content):
    title = get_title(note_content)
    if title == None:
        print("Warning: no note title")
        return graph
    if not graph.has_node(title):
        graph.add_node(title)
    links = get_links(note_content, title)
    for link in links:
        #source is all going to be this note
        if not graph.has_node(link['target']):
            graph.add_node(link['target'])
        graph.add_edge(link['source'], link['target'])
    return graph

def create_outline_from_note(graph, note_title, link_note=True, bodies=None, added_notes=[], current_depth= 0, max_depth=2):
    """
    Creates an outline from notes
    """
    if note_title in added_notes:
        return None
    added_notes.append(note_title)
    neighbors = nx.neighbors(graph, note_title)
    title = note_title
    if link_note:
        title = "[[%s]]"%note_title
    if bodies:
        title += "\n%s"%bodies[note_title]
    if current_depth < max_depth:
        outline = "- %s"%title
        for neighbor in neighbors:
            neighbor_outline, added_notes = create_outline_from_note(graph,
                                                neighbor,
                                                link_note=link_note,
                                                bodies=bodies,
                                                added_notes=added_notes,
                                                current_depth=current_depth+1,
                                                max_depth=max_depth)
            neighbor_outline_lines = neighbor_outline.split("\n")
            for line in neighbor_outline_lines:
                outline += "\n\t%s"%line
    else:
        outline = "- %s"%title
    return outline, added_notes


def create_graph_from_dir(directory):
    files = os.listdir(directory)
    graph = nx.DiGraph()
    for file in files:
        if not file.endswith(".md"):
            continue
        path = os.path.join(directory, file)
        with open(path, 'r') as f:
            content = f.read()
        graph = add_note_to_graph(graph, content)
    return graph

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



def main(directory, root_note, get_bodies=False, link_note=True, outfile=None):
    graph = create_graph_from_dir(directory)
    if get_bodies:
        bodies = get_note_bodies(directory)
        outline, added_notes = create_outline_from_note(graph, root_note, bodies=bodies, link_note=link_note)
    else:
        outline, added_notes = create_outline_from_note(graph, root_note, link_note=link_note)
    if not outfile:
        out_file = os.path.join(directory, "_".join(root_note.split(" "))+"_outline.md")
    else:
        out_file = outfile
    out_content = "# " + root_note + " outline\n" + outline
    with open(out_file, 'w') as f:
        f.write(out_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir')
    parser.add_argument('root')
    parser.add_argument('--bodies', action="store_true")
    parser.add_argument('--nolinks', action="store_false")
    parser.add_argument('--outfile', default=None)
    parsed_args = vars(parser.parse_args())
    directory = os.path.abspath(parsed_args.get("dir"))
    main(directory, parsed_args.get("root"),
        get_bodies=parsed_args.get("bodies"),
        link_note=parsed_args.get("nolinks"),
        outfile=parsed_args.get("outfile"))
