#!/usr/bin/env python

from py2neo import Graph
import json
import csv

class NodeCSV(object):
    def __init__(self):
        self.nodes=[]
        self.links=[]
        self.node_headers=["id","label","group","country"]
        self.link_headers=["source","target","value"]
        self.isLink = False
        
    def patent_to_csv(self, RecordList):
        data={}
        for record in RecordList:
            data['id']=record.n._id
            data['label']= record[0]['patid']
            data['group']= 1
            data['country']= "US"
            #Clone multiple dict to store data in results.
            self.nodes.append(data.copy())
        optflag = self.write_to_csv()
        if optflag==False:
            return False
        else: 
            return True
            
    def inventor_to_csv(self, RecordList):
        data={}
        for record in RecordList:
            data['id']=record.n._id
            data['label']= record[0]['first_name']+" "+record[0]['last_name']
            data['group']= 2
            data['country']= record[0]['country']
            #Clone multiple dict to store data in results.
            self.nodes.append(data.copy())
        optflag = self.write_to_csv()
        if optflag==False:
            return False
        else:
            return True
            
    def links_to_csv(self,RecordList):
        data={}
        results=[]
        for record in RecordList:
            data['source']=record.r.start_node._id
            data['target']=record.r.end_node._id
            data['value']=1
            #Clone multiple dict to store data in results.
            self.links.append(data.copy())
        self.isLink=True
        optflag = self.write_to_csv()
        if optflag==False:
            return False
        else:
            return True
                                
    def write_to_csv(self):
        if self.isLink==False:
            with open("nodes_network.csv",'wb') as outfile:
                writer = csv.writer(outfile, delimiter=';')
                writer.writerow(self.node_headers)
                for item in self.nodes:
                    # Python will default to using the ASCII codec which doesn't support any character codepoint above 127. We need encoded to utf-8
                    writer.writerow([item["id"],item["label"].encode('UTF-8','replace'),item["group"],item["country"].encode('UTF-8','replace')])
                return True
        else:
            with open("links_network.csv",'wb') as outfile:
                writer = csv.writer(outfile, delimiter=';')
                writer.writerow(self.link_headers)
                for item in self.links:
                    writer.writerow([item["source"],item["target"],item["value"]])
                #Set isLink back to false after done.
                self.isLink=False
                return True
            

def create_citation_network(graph):
    inventor_list = graph.cypher.execute("MATCH (n:Inventor) return n")
    patent_list = graph.cypher.execute("MATCH (n:Patent) return n")
    inventor_to_patent_links = graph.cypher.execute("MATCH (i:Inventor)-[r:INVENT]->(n:Patent) return r")
    patent_to_patent_links = graph.cypher.execute("MATCH (i:Patent)-[r:CITEDBY]->(n:Patent) return r")
    
    city_list = graph.cypher.execute("match (n:Inventor)-->(p:Patent) return n.city as city,count(DISTINCT p) as number_of_patents;")
    
    #Build up nodes in csv
    nodecsv= NodeCSV()
    result1=nodecsv.inventor_to_csv(inventor_list)
    result2=nodecsv.patent_to_csv(patent_list)
    i2plinks=nodecsv.links_to_csv(inventor_to_patent_links)
    p2plinks=nodecsv.links_to_csv(patent_to_patent_links)
    
    #Print out results
    if(result1==True):
        print "Writing inventors to csv succeeded !"
    else:
        print "Writing inventors to csv failed !"
        
    if(result2==True):
        print "Writing patents to csv succeeded !"
    else:
        print "Writing patents to csv failed !"
        
    if (i2plinks==True):
        print "Writing inventor_to_patent links to csv succeed !"
    else:
        print "Writing inventor_to_patent links to csv failed !"
    
    if (p2plinks==True):
        print "Writing patent_to_patent links to csv succeed !"
    else:
        print "Writing patent_to_patent links to csv failed !"
    
    if (result1==True and result2==True):
        print "Successfully populated inventors and patents to nodes_network.csv"
    else:
        print "Failed to populate inventors and patents to nodes_network.csv"
        
    if (i2plinks==True and p2plinks==True):
        print "Successfully populated links between nodes_network.csv to links_network.csv"
    else:
       print "Failed to populate links between nodes_network.csv"
        
if __name__ == "__main__":
    graph=Graph()
    create_citation_network(graph)