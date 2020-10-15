import json
def NILpath(tree, entity2path):
    ru = dict()
    son = dict()
    for node in tree:
        ru[node] = 0

    for node in tree:
        for son in tree[node]:
            ru[son] += 1
    path = []
    for node in tree:
        if ru[node] == 0:
            find(node, '/'+node, path, tree)
    return path

def find(node, s, path, tree):
    if len(tree[node]) == 0:
        path.append(s)
        return
    for son in tree[node]:
        find(son, s+'/'+son, path, tree)

def entityTypes(ep):
    et = dict()
    for e in ep:
        et[e]  =set()
        for path in ep[e]:
            types = path[1:].split('/')
            for t in types:
                et[e].add(t)
    return et
# type2son.json = json.load(open('./resources/type2son.json.json', 'r'))
# entity2path = json.load(open('./resources/entity2path_simple.json', 'r'))
# et = entityTypes(entity2path)
# print(et['Chris_Paul'])
# print(len(NILpath(type2son.json, entity2path)))



