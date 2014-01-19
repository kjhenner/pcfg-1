#!/usr/bin/python2
# -*- coding: utf-8 -*-
from __future__ import division
import argparse,nltk
from collections import defaultdict


class pcfg(object):
    def __init__(self):
        self.countDict={}
        self.binary={}
        self.unary={}
        self.probList=[]

    #read from file and output model file
    def train(self,trainFile,modelFile):
        with open(trainFile,'r') as tr:
            trains=tr.readlines()
        #parse bracket format to nltk.Tree
        #trains=map(lambda x:x.lower(),trains)
        trainTrees=map(nltk.Tree.parse,trains)
        #traverse trees to count occurance of grammar
        map(self.traverse,trainTrees)
        print self.countDict
        #calculate probability from counts
        self.calcProb()
        print self.countDict
        #transform countDict to a list for print
        for lhs in self.countDict:
            for rhs in self.countDict[lhs]:
                item=[]
                item.append(lhs)
                item.append(rhs)
                item.append(self.countDict[lhs][rhs])
                #print item
                self.probList.append(item)
        #sort prob list
        sortedList=sorted(self.probList,key=lambda item:item[2],reverse=True)
        #classify rule
        self.classifyRule()
        #print sortedList
        #print sortedList to model file
        with open(modelFile,'w') as mf:
            for item in sortedList:
                mf.write(item[0]+" # ")
                if type(item[1]) is tuple:
                    for elem in item[1]:
                        mf.write(elem+' ')
                elif type(item[1]) is str:
                    mf.write(item[1]+' ')
                mf.write("# "+str(item[2])+'\n')

    #calc probability according to counts
    def calcProb(self):
        for lhs in self.countDict:
            countSum=0
            for rhs in self.countDict[lhs]:
                #print rhs
                countSum+=self.countDict[lhs][rhs]
            for rhs in self.countDict[lhs]:
                self.countDict[lhs][rhs]/=countSum

    #extract nonterminal/unary/binary
    def classifyRule(self):
        for lhs in self.countDict:
            for rhs in self.countDict[lhs]:
                if type(rhs) is tuple:
                    #if len(rhs)==2 and rhs not str:
                    if lhs not in self.binary:
                        self.binary[lhs]={}
                    self.binary[lhs][rhs]=self.countDict[lhs][rhs]
                else:
                    if lhs not in self.unary:
                        self.unary[lhs]={}
                    self.unary[lhs][rhs]=self.countDict[lhs][rhs]



    #traverse the tree
    def traverse(self,t):
        try:
            node=t.node

        except AttributeError:
            #print t
            return

        else:
            # Now we know that t.node is defined

            if node not in self.countDict:
                self.countDict[node]={}

            children=[]
            for child in t:
                if len(t.leaves())==1:
                    children.append(child.lower())
                else:
                    children.append(child.node)
            #print children
            if len(t.leaves())==1:
                key=children[0]
            else:
                key=tuple(children)
            if key not in self.countDict[node]:
                self.countDict[node][key]=1
            else:
                self.countDict[node][key]+=1

            for child in t:
                self.traverse(child)

    #text parser
    def parse(self,text,parseFile):
        sentence=text.split(' ')
        sentence=map(lambda x:x.lower(),sentence)
        #print sentence
        prob,p = self.CYK(sentence)
        textTree,tree=self.listToTree(p)

        with open(parseFile,'w') as pf:
            pf.write(textTree+'\n')
            pf.write(str(prob)+'\n')


        tree.draw()

    def CYK(self,sentence):
        n=len(sentence)
        pi=defaultdict(float)  #DP table
        bp={} #back pointers
        # print "unary:"
        # print self.unary
        # print "binary:"
        # print self.binary

        # print "len sentence:"+str(n)
        # base case
        for i in range(n):
            for lhs in self.unary:
                #print tuple((sentence[i]))
                for rhs in self.unary[lhs]:
                    if rhs==sentence[i]:
                        #print i
                        # print sentence[i]
                        # print self.unary[lhs]
                        pi[i,i,lhs]=self.unary[lhs][sentence[i]]
                    #else:
                    #pi[i,i,lhs]=0

        for width in range(1,n):
            for start in range(n):
                end=start+width
                for X in self.countDict:
                    max_score=0
                    arg=None
                    for R in self.binary:
                        if X==R:
                            for rhs in self.binary[R]:

                                left=rhs[0]
                                right=rhs[1]
                                for s in range(start,end):
                                    if pi[start,s,left] and pi[s+1,end,right]:
                                        score=self.binary[X][rhs]*pi[start,s,left]*pi[s+1,end,right]
                                        if max_score<score:
                                            max_score=score
                                            arg=left,right,s
                    if max_score:
                        pi[start,end,X]=max_score
                        bp[start,end,X]=arg



        #print pi
        #return
        if pi[0,n-1,'S']:
            return (pi[0,n-1,'S'],self.recover_tree(sentence,bp,0,n-1,'S'))
        # else:
        #     max_score=0
        #     arg=None
        #     for lhs in self.countDict:
        #         if max_score<pi[0,n-1,lhs]:
        #             max_score=pi[0,n-1,lhs]
        #             arg=0,n-1,lhs
        #     return self.recover_tree(sentence,bp,*arg)


    def recover_tree(self, x, bp, i, j, X):
        if i == j:
            return [X, x[i]]
        else:
            Y, Z, s = bp[i, j, X]
            return [X, self.recover_tree(x, bp, i, s, Y),
                       self.recover_tree(x, bp, s+1, j, Z)]

    def listToTree(self,p):
        textTree=str(p)
        textTree=textTree.replace('[','(')
        textTree=textTree.replace(']',')')
        textTree=textTree.replace('\'','')
        textTree=textTree.replace(',','')
        tree=nltk.Tree.parse(textTree)
        return (textTree,tree)


if __name__=="__main__":
    parser = argparse.ArgumentParser("Probablistic Context Free Grammar routine.")
    parser.add_argument('-i','--in_file',help='Path for training set',required=False)
    parser.add_argument('-m','--model_file',help='Path for model file',required=True)
    parser.add_argument('-p','--parse_text',help='Text for parsing',required=False)
    parser.add_argument('-pf','--parse_file',help='Output parsing file path',required=False)
    args=parser.parse_args()
    if not args.in_file:
        args.in_file="train.txt"
    pcfgOb=pcfg()
    pcfgOb.train(args.in_file,args.model_file)
    if args.parse_text and args.parse_file:
        pcfgOb.parse(args.parse_text,args.parse_file)
