#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 
#   FILE: AVLTree.py
#   REVISION: November, 2024
#   CREATION DATE: January, 2020
#   AUTHOR: David W. McDonald
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
import json, pickle, hmac, hashlib
from rebert.classes.base.Object import Object
from rebert.classes.data.AVLNode import AVLNode


class AVLTree(Object):
    def __init__(self, name="AVLTree", logger=None):
        super().__init__(name=name, logger=logger)
        self.node = None
        self.height = -1
        self.balance = 0
        return
    
    
    #   Method that relies on JSON
    def load(self, fname=None):
        self.log(f"entering", level="DEBUG")
        if not fname:
            self.log(f"no file name, need to supply a file name", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return
        #   Read the data
        f = open(fname,"r")
        data = json.load(f)
        f.close()
        #   Build the tree
        for node in data:
            self.insert(node=node)
        mesg = f"{len(data)} nodes, {len(self)} data items"
        self.log(f"tree has {mesg}", level="DEBUG")
        self.log(f"returning", level="DEBUG")
        return
    
    #   Method that relies on JSON
    def save(self, fname=None, compact=True):
        self.log(f"entering", level="DEBUG")
        if not fname:
            self.log(f"no file name, need to supply a file name", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return
        #
        # Build a list of the node data objects
        data = list()
        if self.node:
            data = self.node.__get_raw_nodes__()
        self.log(f"have {len(data)} nodes of data to save", level="DEBUG")
        
        if not data:
            self.log(f"no tree data to be saved", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return
        
        f = open(fname,"w")
        mesg = f"saving index '{fname}'"
        #
        #   This option makes the resulting JSON text files 
        #   harder/easier to read, compact has no spaces
        if compact:
            json.dump(data,f)
            self.log(f"{mesg} compact: True", level="DEBUG")
        else:
            json.dump(data,f,indent=4)
            self.log(f"{mesg} compact: False", level="DEBUG")
        f.flush()
        f.close()
        self.log(f"returning", level="DEBUG")
        return
    
    
    
    #   pickle specific
    def read(self, fname="", secret="", signature=""):
        tree = None
        self.log(f"entering", level="DEBUG")
        if not fname:
            self.log(f"no file name, need to supply a file name", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return tree

        if secret and signature:
            f = open(fname,"rb") # "rb" = read binary
            raw_data = f.read()
            f.close()
            str_bytes = bytes(secret,'utf-8')
            sigcheck = hmac.new(str_bytes,raw_data,hashlib.sha256).hexdigest()
            if sigcheck != signature:
                self.log(f"signatures DO NOT match, not loading tree", level="WARN")
                self.log(f"returning", level="DEBUG")
                return tree
            else:
                self.log(f"signatures match, loading data", level="DEBUG")
        else:
            self.log(f"skipping signature check, use caution!", level="WARN")

        f = open(fname,"rb") # "rb" = read binary
        tree = pickle.load(f)
        f.close()
        tree.setLogger(self.getLogger())
        self.log(f"returning", level="DEBUG")
        return tree

    
    
    #   pickle specific
    def write(self, fname="", secret=""):
        self.log(f"entering", level="DEBUG")
        if not fname:
            self.log(f"no file name, need to supply a file name", level="DEBUG")
            self.log(f"returning", level="DEBUG")
            return
        signature = ""
        data = pickle.dumps(self)
        if secret:
            #signature = hmac.new(secret,data,hashlib.sha256).hexdigest()
            str_bytes = bytes(secret,'utf-8')
            signature = hmac.new(str_bytes,data,hashlib.sha256).hexdigest()
        f = open(fname,"wb") # "wb" = write binary
        f.write(data)
        f.close()
        if signature:
            self.log(f"returning, {signature}", level="DEBUG")
        else:
            self.log(f"returning", level="DEBUG")
        return signature

    
    
    #
    #   Traverse the tree to find the insert location
    #
    def insert(self, key=None, value=None, node=None):
        if not node: 
            if not key and not value:
                self.log(f"must supply key and value or node")
                return
        #
        self.log(f"entering", level="DEBUG")
        if node and isinstance(node,dict):
            key = node['key']
            value = node['value']
        if not self.node:
            self.node = AVLNode(key=key,value=value) 
            self.log(f"inserted {key}:{value}", level="DEBUG")
            #   These subtree is clearly balanced, no rebalance
            self.node.left = AVLTree(logger=self.getLogger())
            self.node.right = AVLTree(logger=self.getLogger())
        elif key < self.node: 
            self.log(f"less, inserting into left tree", level="DEBUG")
            self.node.left.insert(key=key,value=value)
            #   When we add to a subtree - then rebalance the tree
            self.__rebalance__() 
        elif key > self.node: 
            self.log(f"greater, inserting into right tree", level="DEBUG")
            self.node.right.insert(key=key,value=value)
            #   When we add to a subtree - then rebalance the tree
            self.__rebalance__() 
        else:
            # add an additional value stored at this key
            self.log(f"'{self.node.data['key']}' additional value at this node", level="DEBUG")
            self.node.append(key=key,value=value)         
        self.log(f"returning", level="DEBUG")
        return


    #
    #   find node, delete item, or whole node
    #
    def delete(self, key=None, value=None):
        if not key:
            return
        if not self.node:
            return
        #   Keep track of whether we delete a *node*
        deletion = False 
        self.log(f"entering", level="DEBUG")
        if self.node == key:
            self.log(f"deleting key '{key}' with value '{value}'", level="DEBUG")
            if value:
                #   Maybe just delete a value at the node
                self.node.delete(key=key, value=value)
                self.log(f"have '{len(self.node)}' values at node", level="DEBUG")
                if len(self.node)==0:
                    #   Nothing remaining at node then delete the node
                    self.__delete_node__(key=key)
                    deletion = True
            else:
                #   Nothing remaining at node then delete the node
                self.__delete_node__(key=key)
                deletion = True
        elif key < self.node:
            self.log(f"less, looking in left tree", level="DEBUG")
            #   This is a call on a tree, AVLTree.delete() method
            deletion = self.node.left.delete(key=key, value=value)  
        elif key > self.node: 
            self.log(f"greater, looking in right tree", level="DEBUG")
            #   This is a call on a tree, AVLTree.delete() method
            deletion = self.node.right.delete(key=key, value=value)
        #
        #   If we actually delete a node, then we rebalance the tree
        if deletion:
            self.__rebalance__()
        self.log(f"returning", level="DEBUG")
        return deletion


    #
    #   Find the tree node key k, and return the AVLNode object
    #   at that location
    #
    def find(self, k=None):
        if not self.node:
            return None
        self.log(f"entering", level="DEBUG")
        result = None
        if self.node == k:
            self.log(f"Found value!", level="DEBUG")
            result = self.node.data['value']
        else:
            if k < self.node and self.node.left:
                self.log(f"less, looking in left tree", level="DEBUG")
                result = self.node.left.find(k)
            if k > self.node and self.node.right:
                self.log(f"greater, looking in right tree", level="DEBUG")
                result = self.node.right.find(k)
        if result:
            self.log(f"returning, found", level="DEBUG")
        else:
            self.log(f"returning, NOT found", level="DEBUG")
        return result


    #
    #   Find all nodes between keys 'lower' and 'upper' and return 
    #   a dictionary, with each key in the range as a key in the dict
    #   and the values as a list of the associated values
    #
    def findRange(self, t=None, lower=None, upper=None):
        result = dict()
        if not t:
            return result
        if not t.node:
            return result
        if not (lower < upper):
            self.log(f"lower '{lower}' must be < to upper '{upper}'", level="DEBUG")
            return
        self.log(f"entering", level="DEBUG")
        if t.node >= lower and t.node < upper:
            self.log(f"found key in range", level="DEBUG")
            result[t.node.data['key']] = t.node.data['value']
        #
        #   Now collect the left and right tree values
        #
        #   Only search the left branch of the tree when there might
        #   be smaller values in the range in that side of the tree
        if t.node >= lower:
            self.log(f"searching left tree", level="DEBUG")
            result.update(self.findRange(t.node.left,lower=lower,upper=upper))
        #
        #   Only search the right branch of the tree when there might
        #   be larger values in the range in that side of the tree
        if t.node <= upper:
            self.log(f"searching right tree", level="DEBUG")
            result.update(self.findRange(t.node.right,lower=lower,upper=upper))
        self.log(f"returning", level="DEBUG")
        return result


    #
    #   Count the number of items in a tree, this includes the number
    #   of items stored at the nodes, not just the number of nodes
    #   This is used to resolve a nasty recursion problem of using the
    #   len() function inside the __len__() method of a class
    #
    def __length__(self, n=None):
        if( n==None ):
            return 0
        count = 0
        if( n.node ):
            #   Count the items in the current node
            count = count + len(n.node)
            #   Count and return everything in the left tree
            count = count + self.__length__(n.node.left)
            #   Count and return everything in the right tree
            count = count + self.__length__(n.node.right)
        return count


    def __delete_node__(self, key=None):
        self.log(f"deleting node with '{key}'", level="DEBUG")
        if( (self.node.left.node==None) and (self.node.right.node==None) ):
            self.log(f"removing empty node, no branches", level="DEBUG")
            # empty node then just delete it
            self.node = None 
        # only one subtree, take that 
        elif( self.node.left.node==None ):
            self.log(f"replacing with right.node", level="DEBUG")
            self.node = self.node.right.node
        elif( self.node.right.node==None ):
            self.log(f"replacing with left.node", level="DEBUG")
            self.node = self.node.left.node
        # both children present - replace with successor
        else:
            self.log(f"replacing with successor node", level="DEBUG")
            rnode = self.__successor__(self.node)
            if( rnode ):
                # use that node to replace the key and value
                self.log(f"replacing {self.node.data['key']} with {rnode.data['key']}", level="DEBUG")
                self.node.data['key'] = rnode.data['key']
                self.node.data['value'] = rnode.data['value']
                rnode.data['value'] = list()
                # replaced the node, now delete the key from right child
                self.node.right.delete(rnode.data['key'])
        return


    def __rebalance__(self):
        if not self.node:
            return
        # key inserted. Let's check if we're balanced
        self.log(f"balancing tree at node '{self.node.data['key']}'", level="DEBUG")
        self.__update_heights__(False)
        self.__update_balances__(False)
        while( (self.balance < -1) or (self.balance > 1) ): 
            if( self.balance > 1 ):
                if( self.node.left.balance < 0 ):  
                    self.node.left.__rotate_left__()
                    self.__update_heights__()
                    self.__update_balances__()
                self.__rotate_right__()
                self.__update_heights__()
                self.__update_balances__()
                
            if( self.balance < -1 ):
                if( self.node.right.balance > 0 ):  
                    self.node.right.__rotate_right__()
                    self.__update_heights__()
                    self.__update_balances__()
                self.__rotate_left__()
                self.__update_heights__()
                self.__update_balances__()
        return


    def __update_heights__(self, recurse=True):
        if( self.node==None ):
            self.height = -1
            return
        lheight = 0
        rheight = 0
        if( recurse ):
            if( self.node.left!=None ):
                self.node.left.__update_heights__()
                lheight = self.node.left.height
            if( self.node.right!=None ):
                self.node.right.__update_heights__()
                rheight = self.node.right.height
        if( self.node.left!=None ):
            lheight = self.node.left.height
        if( self.node.right!=None ):
            rheight = self.node.right.height
        self.height = max(lheight,rheight) + 1
        return
    
    
    def __update_balances__(self, recurse=True):
        if( self.node==None ):
            self.balance = 0
            return
        lheight = 0
        rheight = 0
        if( recurse ):
            if( self.node.left!=None ):
                self.node.left.__update_balances__()
            if( self.node.right!=None ):
                self.node.right.__update_balances__()
        if( self.node.left!=None ):
            lheight = self.node.left.height
        if( self.node.right!=None ):
            rheight = self.node.right.height
        self.balance = lheight - rheight
        return



    def __rotate_right__(self):
        # Rotate left pivoting on self
        self.log(f"rotate right '{self.node.data['key']}'", level="DEBUG")
        node = self.node 
        nodeLeftNode = self.node.left.node 
        nodeLeftNodeRightNode = nodeLeftNode.right.node 

        self.node = nodeLeftNode
        nodeLeftNode.right.node = node
        node.left.node = nodeLeftNodeRightNode 
        return
    


    def __rotate_left__(self):
        # Rotate left pivoting on self
        self.log(f"rotate left '{self.node.data['key']}'", level="DEBUG")
        node = self.node 
        nodeRightNode = self.node.right.node 
        nodeRightNodeLeftNode = nodeRightNode.left.node 

        self.node = nodeRightNode 
        nodeRightNode.left.node = node 
        node.right.node = nodeRightNodeLeftNode
        return

    #
    #   Find the smallest value key in the RIGHT child of node
    #
    def __successor__(self, node=None):
        if node:
            node = node.right.node
            while( node.left ):
                self.log(f"traversing '{node.data['key']}'")
                if node.left.node: 
                    node = node.left.node  
        if node:
            self.log(f"smallest is: '{node.data['key']}'", level="DEBUG")
        else:
            self.log(f"node is 'None'", level="DEBUG")
        return node
    
    
    #
    #   Get the raw dictionaries of the tree as a list
    #
    def __get_raw_nodes__(self):
        data = list()
        self.log(f"entering", level="DEBUG")
        if self.node:
            data = self.node.__get_raw_nodes__()
        self.log(f"returning, {len(data)} nodes", level="DEBUG")
        return data

    ##
    #
    #   This implements the dictionary/list style access/fetch 
    #
    def __getitem__(self, k): 
        return self.find(k=k)
    
    ##
    #
    #   This implements the dictionary/list style insertion 
    #
    def __setitem__(self, k, v):
        self.insert(key=k, value=v)
        return

    ##
    #
    #   This implements the use of the 'in' operator 
    #
    def __contains__(self, k): 
        return self.find(k=k)
    
    ##
    #
    #   This implements the use of the 'del' function in a dictionary style 
    #
    def __delitem__(self, k):
        self.delete(key=k)
        return

    ##
    #
    #   This returns the number of things *stored* in the tree. This is 
    #   not the same as the number of nodes in the tree, or the height.
    #   This uses the __length__() method, calling it on this tree (self)
    #   to resolve a nasty recursion problem when using the len() function
    #   inside the __len__() method of a class 
    #
    def __len__(self):
        length = 0
        if( self.node ):
            length = self.__length__(self)
        return length


    def __repr__(self):
        count = len(self)
        #obj = super().__repr_()
        obj = repr(super()).partition(' ')[2]
        obj = obj.partition(',')[0]
        r = f"<instance of {obj} with {count} items>"
        #r = str()
        #if( self.node and self.node.left ):
        #    r = r + str(self.node.left)
        #if( self.node ):
        #    if( r ):
        #        r = r+"\n"+str(self.node)
        #    else:
        #        r = r + str(self.node)
        #if( self.node and self.node.right ):
        #    if( r ):
        #        r = r+"\n"+str(self.node.right)
        #    else:
        #        r = r + str(self.node.right)
        return r

if __name__ == '__main__':
    print("AVLTree.py is a class with no main()")





