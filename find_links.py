import os
import json
import re
import pdb
import requests
from datetime import datetime


'''
 test2 = [
     ...:   {
     ...:     "source": "node 100",
     ...:     "target": "node 200",
     ...:     "type": "suit"
     ...:   },
     ...:   {
     ...:         "source": "node 1",
     ...:          "target": "node 2",
     ...:          "type": "licensing"}
     ...: ]
'''
#r= requests.put("https://api.myjson.com/bins/5yjbk", json=test2)

if __name__=="__main__":
    path = "/Users/zaaron/Downloads/Notes_Test/"
    files = os.listdir(path)
    links = []
    # Create Edges
    for file in files:
        created = datetime.fromtimestamp(os.stat(path+file).st_birthtime)
        modified = datetime.fromtimestamp(os.path.getmtime(path+file))
        if file[-2:] != 'md':
            print("skipping ending:" + file[-2:])
            continue
        with open(path+file) as f:
            content = f.read()
            name = file.split(".")[0]
            refs = re.findall('\[\[.*?\]\]', content)
            refs = [l.strip('[[').strip(']]') for l in refs]
            for ref in refs:
                links.append({"source":name, "target":ref, "type":"suit"})

            links.append({"source":name, "target":name, "type":"suit"})
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
    # Notes over time


    #upload links
    r = requests.put("https://api.myjson.com/bins/5yjbk", json=links)
