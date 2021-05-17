from collections import defaultdict
import re
import numpy as np
import os
import configure


# Class Attribute that has variables: type, text, start, end
class Attribute:
    def __init__(self, tag, text, start, end):
        self.tag = tag
        self.text = text
        self.start = start
        self.end = end

    def __str__(self):
        return f'{self.tag}, {self.text}, [{self.start}, {self.end}]'

    def __key(self):
        return self.tag, self.text, self.start, self.end

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Attribute):
            return self.__key() == other.__key()
        return NotImplemented


# Class Node that contain variables: indexes (which is the word index in the snippets, a Node may contain a phrase
# which is a list of word indexes), parent node and children nodes.
class Node:
    def __init__(self):
        self.indexes = []
        self.parent = None
        self.children = []
        self.dep = None


reg_map = defaultdict(list)

# use regular expression to extract all the attributes
# read in the regex pattern (the regex patterns is extended from MedXN: https://github.com/OHNLP/MedXN


def get_reg(reg_path):
    var_map = {}
    with open(reg_path, 'r') as patterns:
        for line in patterns:
            if line.startswith('#') or len(line) == 0 or re.search(r'^\s', line):
                continue
            if line.startswith('@'):
                var_map[line.split('::')[0]] = line.split('::')[1].strip().replace('\\\\', '\\')
            else:
                tag = line.split('::')[0].strip()
                pat = line.split('::')[1].strip().replace('\\\\', '\\')
                for key, value in var_map.items():
                    pat = pat.replace(key, value)
                reg_map[tag].append(pat)


# remove duplicates
def remove_duplicate(attr):
    temp = []
    ret = []
    spans = set()
    for item in attr:
        # remove duplicates
        span = f"{item.tag}|{item.start}|{item.end}"
        if span in spans:
            continue
        spans.add(span)
        temp.append(item)

    # remove overlapped
    for i in range(len(temp)):
        is_overlap = False
        for j in range(len(temp)):
            if i == j:
                continue
            if temp[i].tag == temp[j].tag and temp[i].start >= temp[j].start and temp[i].end <= temp[j].end:
                is_overlap = True
                break
        if not is_overlap:
            ret.append(temp[i])
    return ret


# extract the attribute using reg_map
def extract_attributes(text):
    attr = []
    for key, value in reg_map.items():
        gnum = 0
        aTag = key
        if '%' in key:
            aTag = key.split('%')[0].strip()
            gnum = int(key.split('%')[1].strip())
        for pat in value:
            for item in re.finditer(pat, text, re.I):
                attr.append(Attribute(aTag, item.group(gnum), item.start(gnum), item.end(gnum)))
    return remove_duplicate(attr)


# extract attributes within the identified treatment entity (e.g. CUI: C2912166: hydroxychloroquine sulfate 200 MG)
def local_extract(snippet):
    for entity in snippet['entities']:
        attrs = extract_attributes(entity['ngram'])
        for attr in attrs:
            key = 'has_' + attr.tag
            if key in entity.keys():
                entity[key].append(attr.text)
            else:
                entity[key] = [attr.text]


# find_spans helper function
def find_span(doc, attr):
    start_list = [i.idx for i in doc]
    end_list = [i.idx + len(i) for i in doc]
    start = 0
    for i in start_list:
        if i > attr.start:
            break
        start = i
    end = 0
    for i in reversed(end_list):
        if i < attr.end:
            break
        end = i
    return doc.char_span(start, end)


# 1. deal with the cases that extracted attributes are part of a token: e.g. 500 mg/day, where "500 mg" is the
# strength, "day" is the frequency
# 2. expand the span to include adjacent attributes, this is in accordance with the
# heuristic rule for attribute association
def find_spans(doc, attrs):
    span_map = {}
    for attr in attrs:
        span_map[attr] = find_span(doc, attr)
        print(span_map[attr])
        print('the span found for attribute ' + attr.text + ' is ' + span_map[attr].text)
    # merge span
    # sort the attributes based on the start position.
    temp = sorted(span_map.items(), key=lambda x: x[1].start)
    merged_map = {}

    # extract the first attribute's start and end position
    start = temp[0][1].start
    end = temp[0][1].end
    temp_attr = []
    for item in temp:
        if item[1].start <= end and item[0].tag != 'negation':
            end = item[1].end
            temp_attr.append(item[0])
        else:
            for attr in temp_attr:
                merged_map[attr] = doc[start:end]
            start = item[1].start
            end = item[1].end
            temp_attr.clear()
            temp_attr.append(item[0])
    for attr in temp_attr:
        merged_map[attr] = doc[start:end]
    return merged_map


# associate treatment-attributes based on relative text position.
# the snippet will be simplified after association, which
def local_associate(snippet, attrs, doc):
    index_map = {}
    for token in doc:
        if "ENTITY" in token.text:
            index_map[token.text] = token.i

    # store the assigned attributes
    to_remove = set()

    span_map = find_spans(doc, attrs)

    for key, value in span_map.items():
        print(key.text + '\t' + value.text)

    if snippet['entities'] is None:
        return attrs

    for attr in attrs:
        span = span_map[attr]
        # the attrs associate with the lateral entity prior to previous entity
        for entity in reversed(snippet['entities']):
            if 'id' not in entity.keys():
                continue
            index = -100
            for key, value in index_map.items():
                if entity['id'] in key:
                    index = value
                    break
            if index + 1 == span.start or span.end == index:
                key = 'has_' + attr.tag
                if key in entity.keys():
                    entity[key].append(attr.text)
                else:
                    entity[key] = [attr.text]
                to_remove.add(span)
                break

    # remove the assigned attributes from the text snippets as well
    mask = np.ones(len(doc.text), np.bool)
    for item in to_remove:
        mask[[x for x in range(item.start_char, item.end_char)]] = 0
    new_text = ''.join([doc.text[i] for i in range(len(doc.text)) if mask[i]])
    new_text = re.sub(r'\s+', ' ', new_text)
    new_text = re.sub(r'\s+,', ',', new_text)
    return new_text


# dependency parser-based association, mark if the dependency is conj
# determine the root of the tree
def construct_tree(doc):
    token_node = {}
    root = None
    # mapping between token and node, after mapping, each node only have the indexes assigned.
    for token in doc:
        temp_node = Node()
        temp_node.indexes.append(token.i)
        temp_node.dep = token.dep_
        token_node[token] = temp_node
    # connect the parent and children
    for token in doc:
        if token.head == token:
            root = token_node[token]
        temp_node = token_node[token]
        temp_node.parent = token_node[token.head]
        for child in token.children:
            temp_node.children.append(token_node[child])
    return root


def find_path(root, path, node):
    if root is None:
        return False
    path.append(root)
    if root == node:
        return True
    for child in root.children:
        if find_path(child, path, node):
            return True
    path.pop()
    return False


# find common ancestor
def find_common_ancestor(root, node1, node2):
    path1 = []
    path2 = []

    if not find_path(root, path1, node1) or not find_path(root, path2, node2):
        if node1 is None:
            print("node1 is none")
        if node2 is None:
            print("node2 is none")
        return None
    pointer = 0
    while pointer < len(path1) and pointer < len(path2):
        if path1[pointer] != path2[pointer]:
            break
        pointer += 1
    return path1, path2, path1[pointer - 1]


def find_ancestor_loc(path, ancestor):
    pointer = 0
    for node in path:
        if node == ancestor:
            break
        pointer += 1
    return pointer


# merge two nodes that belong to a single attr
# it will return the converted graph and the merged node
def merge_nodes_helper(root, node1, node2):
    if node1 == node2:
        return node1, root

    if find_common_ancestor(root, node1, node2) is None:
        return None, root
    path1, path2, ancestor = find_common_ancestor(root, node1, node2)

    newNode = Node()
    newNode.indexes.extend(node1.indexes)
    newNode.indexes.extend(node2.indexes)

    # append the indexes of nodes from ancestor to node1

    pointer = find_ancestor_loc(path1, ancestor) + 1
    while pointer < len(path1) - 1:
        newNode.indexes.extend(path1[pointer].indexes)
        pointer += 1

    # append the indexes of nodes from ancestor to node2

    pointer = find_ancestor_loc(path2, ancestor) + 1
    while pointer < len(path2) - 1:
        newNode.indexes.extend(path2[pointer].indexes)
        pointer += 1

    # determine the parent, children of newNode
    if ancestor == node1 or ancestor == node2:
        if ancestor == root:
            root = newNode
            print("revised root is ", root.indexes)
            root.parent = root
        else:
            newNode.parent = ancestor.parent
            newNode.dep = ancestor.dep
            ancestor.parent.children.remove(ancestor)
            ancestor.parent.children.append(newNode)
    else:
        newNode.parent = ancestor
        one_children = path1[find_ancestor_loc(path1, ancestor) + 1]
        if one_children.dep == 'conj':
            newNode.dep = 'conj'
        ancestor.children.remove(one_children)
        other_children = path2[find_ancestor_loc(path2, ancestor) + 1]
        if other_children.dep == 'conj':
            newNode.dep = 'conj'
        ancestor.children.remove(other_children)
        if newNode.dep is None:
            newNode.dep = 'not_conj'
        ancestor.children.append(newNode)

    # the children of node1 and node2 should not be in the path
    for child in node1.children:
        if (child in path1) or (child in path2):
            continue
        newNode.children.append(child)
        child.parent = newNode

    for child in node2.children:
        if (child in path1) or (child in path2):
            continue
        newNode.children.append(child)
        child.parent = newNode

    return newNode, root


def index_2_node(node, index):
    if node is None:
        return None
    if index in node.indexes:
        return node

    for child in node.children:
        temp = index_2_node(child, index)
        if temp:
            return temp
    return None


# merge nodes that belong to a single attr, and return that node
def merge_nodes(doc, root, span):
    print(f'start:\tmerging the attr: {span.text}')
    nodes = []
    for token in span:
        nodes.append(index_2_node(root, token.i))
    print("done:\tconvert token to node")
    if len(nodes) == 0:
        print("error:\tdid not find any node for token")
    if len(nodes) == 1:
        return nodes[0], root

    # temp_node is the temporal merged node
    temp_node = nodes[0]

    for node in nodes:
        # handle exception, when temp_node is None
        if temp_node is None:
            return temp_node, root
        print("merging nodes:\t", [doc[i] for i in node.indexes], [doc[i] for i in temp_node.indexes])
        temp_node, root = merge_nodes_helper(root, temp_node, node)
    # again handle exceptions
    if temp_node is None:
        return temp_node, root
    print("merge complete:\t", [doc[i] for i in temp_node.indexes])
    return temp_node, root


# find nearest entity
def find_nearest_entity(root, attr_node, entity_indexes, doc):
    print("looking for the nearest intervention entity:\t", [doc[i] for i in attr_node.indexes],
          [doc[i] for i in entity_indexes])
    # deal with the case that there is only one entity in the snippet
    if len(entity_indexes) == 1:
        print("nearest intervention entity found:\t", [doc[i] for i in entity_indexes])
        return entity_indexes

    entity_nodes = []
    entity_map = {}

    print(doc.text)
    for index in entity_indexes:
        entity_node = index_2_node(root, index)
        if entity_node is None:
            print("cannot find the node for", doc[index].text)
            continue
        entity_nodes.append(entity_node)
        entity_map[entity_node] = index
    dis_dict = {}
    for entity_node in entity_nodes:
        path1, path2, ancestor = find_common_ancestor(root, entity_node, attr_node)
        loc1 = find_ancestor_loc(path1, ancestor)
        loc2 = find_ancestor_loc(path2, ancestor)

        dis = 0
        for pointer in range(loc1 + 1, len(path1)):
            if path1[pointer].dep != 'conj':
                dis += 1

        for pointer in range(loc2 + 1, len(path2)):
            if path2[pointer].dep != 'conj':
                dis += 1
        dis_dict[entity_node] = dis
    sorted_dis_dict = sorted(dis_dict.items(), key=lambda x: x[1])

    # the nearest entity/entities is stored in result
    result = []
    min_dis = sorted_dis_dict[0][1]
    for item in sorted_dis_dict:
        if item[1] <= min_dis:
            result.append(entity_map[item[0]])
        else:
            break
    print("nearest intervention entity found:\t", [doc[i] for i in result])
    return result


# associate the attrs to entity
def associate_entity(doc, root, attrs):
    entity_indexes = []
    attr_map = {}
    if len(attrs) == 0:
        return attr_map
    for token in doc:
        if "ENTITY" in token.text:
            entity_indexes.append(token.i)
    span_map = find_spans(doc, attrs)
    for attr in attrs:
        attr_node, root = merge_nodes(doc, root, span_map[attr])
        # handle exception
        if attr_node is None:
            return None
        attr_map[attr] = []
        # handle exception
        temp_map = find_nearest_entity(root, attr_node, entity_indexes, doc)
        if temp_map is None:
            return None
        attr_map[attr].extend(temp_map)
    return attr_map


def reverse(attr_map, doc):
    rev_attr = {}
    for key, value in attr_map.items():
        for ent in value:
            text = doc[ent].text
            if text in rev_attr.keys():
                rev_attr[text].append(key)
            else:
                rev_attr[text] = [key]
    return rev_attr


def run(snippets, nlp):
    print('-' * 25 + 'extracting attributes' + '-' * 25)

    # retrieve the regular expression file
    get_reg(os.path.join(configure.RESOURCE_PATH, 'attribute_patterns.txt'))

    # process the snippets
    for snippet in snippets:
        print('processing:\t', snippet['processed'])

        if len(snippet['entities']) == 0:
            continue

        # first step: local extract
        local_extract(snippet)

        attrs = extract_attributes(snippet['representation'])
        if len(attrs) == 0:
            continue

        doc = nlp(snippet['representation'])
        # second step: local association
        new_representation = local_associate(snippet, attrs, doc)
        doc = nlp(new_representation)
        new_attrs = extract_attributes(new_representation)

        if len(new_attrs) == 0:
            continue

        # third step: dependency-parser based extraction
        root = construct_tree(doc)
        attr_map = associate_entity(doc, root, new_attrs)
        if attr_map is None:
            continue
        attr_map = reverse(attr_map, doc)

        for entity in snippet['entities']:
            if entity['id'] not in attr_map.keys():
                continue
            for attr in attr_map[entity['id']]:
                key = 'has_' + attr.tag
                if key in entity.keys():
                    entity[key].append(attr.text)
                else:
                    entity[key] = [attr.text]

