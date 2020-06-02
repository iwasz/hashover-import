#!/usr/bin/env python
import sys
import sqlite3
import xml.etree.ElementTree as ET
from anytree import Node, RenderTree, AsciiStyle, NodeMixin
import anytree

conn = sqlite3.connect('hashover.sqlite')
c = conn.cursor()


def storeComment(thread, order, body, date, author, website):
    c.execute("INSERT INTO comments (domain, thread, comment, body, date, name, website) VALUES ('all', ?, ?, ?, ?, ?, ?)",
              (thread, order, body, date, author, website))


class CommentId(NodeMixin):
    def __init__(self, hsId, wpId,  parent=None, children=None):
        super(CommentId, self).__init__()
        self.hsId = hsId
        self.wpId = wpId
        self.parent = parent
        if children:  # set children only if given
            self.children = children


def findMaxHsId(node):
    '''Find the biggest hsId in this level'''

    maxHsId = 0
    # for c in anytree.search.find(node, maxlevel=1):
    for c in node.children:
        if c.hsId > maxHsId:
            maxHsId = c.hsId

    return maxHsId


def getHsIdStr(node):
    '''String representation of hashover comment IDs'''
    nodeStr = str(node.hsId)

    while node.parent != None:
        node = node.parent

        # if we are at the root, we break since root is a fake comment
        if node.hsId == 0:
            break

        nodeStr = str(node.hsId) + '-' + nodeStr

    return nodeStr


ns = {'wp': 'http://wordpress.org/export/1.2/'}
currentTree = ET.parse('wordpress.xml')
root = currentTree.getroot()

for item in root.iter('item'):
    postName = item.find('wp:post_name', ns)
    category = item.find('category')

    finalName = ''

    if category != None:
        finalName = finalName + category.get('nicename') + '-'

    if postName != None and postName.text != None:
        finalName = finalName + postName.text

    print('Storing post : {}'.format(finalName))

    # Fake comment as a root of all other comments for this post
    root = CommentId(0, 0)

    for comment in item.findall('wp:comment', ns):
        body = comment.find('wp:comment_content', ns).text
        wpId = int(comment.find('wp:comment_id', ns).text)
        parent = comment.find('wp:comment_parent', ns)

        if parent != None and parent.text != '0':
            par = anytree.search.findall(
                root, filter_=lambda node: node.wpId == int(parent.text))
            maxHsId = findMaxHsId(par[0])
            cNode = CommentId(maxHsId+1, wpId, parent=par[0])

        else:
            maxHsId = findMaxHsId(root)
            cNode = CommentId(maxHsId+1, wpId, parent=root)

        author = comment.find('wp:comment_author', ns).text
        date = comment.find('wp:comment_date', ns).text
        website = comment.find('wp:comment_author_url', ns)

        if website != None:
            website = website.text

        storeComment(finalName, getHsIdStr(cNode), body, date, author, website)

conn.commit()
conn.close()
