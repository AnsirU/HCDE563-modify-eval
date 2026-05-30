#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: AVLNode.py
#   REVISION: November, 2024
#   CREATION DATE: January, 2020
#   AUTHOR: David W. McDonald
#
#   This class supports the implementation of the AVLTree. This class 
#   implments the data storage at each node in the tree. Keeping track of the
#   'key' and a list of potential values as 'value'.
#   
#   Implementation of an AVLTree - which is s self balancing binary tree
#   This could be useful for building indices. This implementation assumes that
#   there could be duplicates of a node "key" but that would have different 
#   values - thus the list of values.
#
#   This implementation was inspired by some code that I saw out on the internet.
#
#   The code below fixes several crashing situations in the examples. As well,
#   the code below facilitates saving/restoring the indexed content, and
#   supports multiple values to be associated with any key.
#
#   The November 2024 revision was to integrate this with the Rebert code base
#   for use with the JSON Data Folder Index objects. In that case this is used
#   to index values fields of a JSON Data Folder object.
#
#   The AVLTree code was also rewritten to use JSON as the save/restore data 
#   structure, removing the use of pickle for storing the data structure. The
#   AVLNode code now includes implementation for comparisons, that simplifies
#   inserting and finding. The code was also broken into two files to stay
#   with the one object one file style of coding.
#   
#   Copyright by Author. All rights reserved. Not for reuse without express permissions.
#
from rebert.classes.base.Object import Object


class AVLNode(Object):
    def __init__(self, key=None, value=None, node=None):
        super().__init__(name="AVLNode")
        self.data = dict()
        if node and isinstance(node,dict):
            self.data=node
        else:
            self.data['key'] = key
            if isinstance(value,list):
                self.data['value'] = value
            else:
                self.data['value'] = list()
                self.data['value'].append(value)
        self.left = None
        self.right = None
        return
    
    #
    #   Searches the nodes in the tree for the correct location
    #   to append the value.
    #
    def append(self, key=None, value=None, node=None):
        if isinstance(node,dict):
            key = node['key']
        if self.data['key']==key or key==None:
            if isinstance(node,dict):
                for value in node['value']:
                    if value not in self.data['value']:
                        self.data['value'].append(value)
            else:
                if value not in self.data['value']:
                    self.data['value'].append(value)
        else:
            if self.left and self.left.node:
                self.left.node.append(key,value,node)
            if self.right and self.right.node:
                self.right.node.append(key,value,node)
        return
            

    #
    #   Searches the nodes in the tree for the right location and
    #   removes the specified value.
    #
    #   Note: this delete() method is for deleting a specific value
    #   to delete all values associated with a given key use the
    #   del operator (see below)
    #
    def delete(self, key=None, value=None):
        if self.data['key']==key or key==None:
            nv = list()
            # run through the list of items and remove 'value'
            for item in self.data['value']:
                if value!=item:
                    nv.append(item)
            self.data['value'] = nv
        else:
            if (key < self.data['key']) and self.left and self.left.node:
                del self.left.node[k]
            if (key > self.data['key']) and self.right and self.right.node:
                del self.right.node[k]
        return

    #
    #   Get the raw dictionaries of each node in subtrees
    #
    def __get_raw_nodes__(self):
        data = list()
        if self.left.node:
            #   The result of the call on the left tree is a list
            data.extend(self.left.node.__get_raw_nodes__())
        if self.data:
            #   Just append, because this is just a dict
            data.append(self.data)
        if self.right.node:
            #   The result of the call on the right tree is a list
            data.extend(self.right.node.__get_raw_nodes__())
        return data



#
#   Implementation of comparison is based on the values of the keys
#
    #   implement == comparison
    def __eq__(self, other):
        if isinstance(other,AVLNode):
            return (self.data['key'] == other.data['key'])
        else:
            return (self.data['key'] == other)
        return
    
    #   implement < comparison
    def __lt__(self, other):
        if isinstance(other,AVLNode):
            return (self.data['key'] < other.data['key'])
        else:
            return (self.data['key'] < other)
        return
    
    #   implement <= comparison
    def __le__(self, other):
        if isinstance(other,AVLNode):
            return (self.data['key'] <= other.data['key'])
        else:
            return (self.data['key'] <= other)
        return
    
    #   implement > comparison
    def __gt__(self, other):
        if isinstance(other,AVLNode):
            return (self.data['key'] > other.data['key'])
        else:
            return (self.data['key'] > other)
        return
    
    #   implement >= comparison
    def __ge__(self, other):
        if isinstance(other,AVLNode):
            return (self.data['key'] >= other.data['key'])
        else:
            return (self.data['key'] >= other)
        return
    
    #   implement != comparison
    def __ne__(self, other):
        if isinstance(other,AVLNode):
            return (self.data['key'] != other.data['key'])
        else:
            return (self.data['key'] != other)
        return
    
    def __getitem__(self, k):
        if self.data['key']==k:
            return self.data['value']
        else:
            if (k < self.data['key']) and self.left and self.left.node:
                return self.left.node[k]
            if (k > self.data['key']) and self.right and self.right.node:
                return self.right.node[k]
        return
    
    def __setitem__(self, k, v):
        if self.data['key']==k:
            if v not in self.data['value']:
                self.data['value'].append(v)
        else:
            if (k < self.data['key']) and self.left and self.left.node:
                self.left.node[k] = v
            if (k > self.data['key']) and self.right and self.right.node:
                self.right.node[k] = v
        return
    
    def __delitem__(self, k):
        if self.data['key']==k:
            self.data['key'] = None
            self.data['value'] = list()
        else:
            if (k < self.data['key']) and self.left and self.left.node:
                del self.left.node[k]
            if (k > self.data['key']) and self.right and self.right.node:
                del self.right.node[k]
        return
    
    def __iter__(self):
        return iter(self.data['value'])
    
    def __len__(self):
        return len(self.data['value'])
    
    def __repr__(self):
        #r = dict()
        #r[self.data['key']] = self.data['value']
        # sort of 'dict' like stringification
        r = f"'{self.data['key']}':{str(self.data['value'])}" 
        return r


if __name__ == '__main__':
    print("AVLNode.py is a class with no main()")





