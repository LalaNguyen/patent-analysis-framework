"""
    db-client
    ~~~~~~~~~~~~~~~
    Provides more functions to work with specific xml 4.5 DTD of US patents. 

"""
import requests
import json
import ijson
import copy
from itertools import izip
import time, sys
import re

ENTRY_POINT = 'http://localhost:5000'
FILE_NAME = "data.json"   
NEO4J_DATABASE = 'http://localhost:7474/db'

class HTTPService(object):
    
    def __init__(self,entry):
        self.entry_point=entry
        
    def _get(self,resource):
        """Perform the actual GET.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
        """
        r = requests.get(self.endpoint(resource))
        return r.json()
        
    def _post(self,resource, data):
        """Perform the actual POST.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
            :param data(list): list of patent data that are parsed from json.
    
        Returns: 
            :param r(dict): json object of the response
        """
        headers = {'Content-Type':'application/json'}
        
        # Convert list data to json format
        query = json.dumps(data, indent=4)
        return requests.post(self.endpoint(resource),query,headers=headers)
    
    def _put(self,resource, data,etag):
        
        headers = {'Content-Type':'application/json','If-Match':etag}
        
        query = json.dumps(data, indent=4)
        r = self.endpoint(resource)
        #print query
        return requests.put(r,query,headers=headers)
   
    def _delete_all(self,resource):
        """Perform the actual DELETE.
    
        Args:
            :param resource(str): endpoint of connection to be deleted. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
        """
        r = requests.delete(self.endpoint(resource))
        return r
        
    def endpoint(self,resource):
        """Attach the resource endpoint to host.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param str(str): concated string of final destination
        """
        return '%s/%s/' % (self.entry_point, resource)
                
    def _find(self,resource,query):
        resource = self.entry_point+'/'+resource+query
        r = requests.get(resource)
        return r.json()
        
class Neo4jDBConnector(HTTPService):
    """Create connector that wraps around HTTP methods before 
       forwarding to actual HTTP services for communication with 
       different database rest api.
    
    Public functions:
    
    * ``post``
    
    * ``get``
    
    * ``findID``

    """
        
    def get(self,resource):
       """Perform the actual GET.
   
       Args:
           :param resource(str): endpoint of connection. E.g people, inventors
   
       Returns: 
           :param r(dict): json object of the response
       """
       r = self._get(resource)
       return r
       
    def post(self,data,resource,label):
        """POST bulk of list, also work with single list.
    
        Args:
            :param data(list): list of patent data that are parsed from json.
            :param resource(str): endpoint of connection. E.g people, inventors
            :param label(str): Label of node. E.g People, Patent
    
        Returns: 
            :param r(int): status_code
            
        """
        count = 0;
        # Begin transaction
        if label == "Inventor":
            start = time.time()
            print 'Posting statements to Neo4j DB server [ ]',
            print '\b'*3,
            sys.stdout.flush()
            for i in range(len(data)):
                statements = []              
                for item in data[i]["inventors"]:                    
                    s1="MERGE (a:Inventor {first_name:\"%s\",last_name:\"%s\", city:\"%s\", country:\"%s\"})" %(item['first-name'],item['last-name'],item['city'],item['country'])
                    s2="MERGE (b:Patent{patid:\"%s\"})" %data[i]["patid"]
                    s3="MERGE (a)-[:INVENT]->(b)"
                    s = s1+s2+s3   
                    query = {
                        "statement": s,                             
                    }
                    count = count +1
                    sys.stdout.write(spinner.next())
                    statements.append(query)
                    sys.stdout.flush()
                    time.sleep(0)
                    sys.stdout.write('\b')
                    sys.stdout.flush()
                statements = {"statements":statements}
                a = self._post(resource+"/commit",statements)
                if not a.json()["errors"]:
                    pass
                    #print '\bOK] -  ', 'Completed in ', time.time()-start
                else:
                    print '\bERROR] -  ', a.json()["errors"][0]["message"]    
            print ' \bOK] -  ', count, ' inventor statements created  in ', time.time()-start
            
        if label == "Patent":
            print 'Posting statements to Neo4j DB server [ ]',
            print '\b'*3,
            sys.stdout.flush()
            start = time.time()
            for i in range(len(data)):    
                statements = []            
                for item in data[i]["citations"]:                    
                    s1="MERGE (c:Patent{patid:\"%s\"})" % item["doc-number"]
                    s2="MERGE (p:Patent{patid:\"%s\"})" % data[i]["patid"]
                    s3="MERGE (c)-[r:CITEDBY]->(p)"
                    s = s1+s2+s3   
                    query = {
                        "statement": s,                             
                    }
                    count = count +1
                    sys.stdout.write(spinner.next())
                    statements.append(query)
                    sys.stdout.flush()
                    time.sleep(0)
                    sys.stdout.write('\b')
                    sys.stdout.flush()
                statements = {"statements":statements}
                a = self._post(resource+"/commit",statements)
                if not a.json()["errors"]:
                    pass
                    #print '\bOK] -  ', 'Completed in ', time.time()-start   
                else:
                    print '\bERROR] -  ', a.json()["errors"][0]["message"]
            print ' \bOK] -  ', count, ' patent statements created  in ', time.time()-start

            
            #print a.json()
        return 0
        
    def findID(self,resource,key, label):
        """Return document of specific ID from a resource.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
            :param key(str): an ID of document within resource/collection.
            
        Returns: 
            :param r(dict): json object of the response
            
        """
        s = "MATCH (p:%s { patid:{key}}) RETURN p" %label
        query = {
            "query" : s,
            "params" : {
                "key":key
            }
        }
        r = self._post(resource,query)
        return r

       
class MongoDBConnector(HTTPService):
    """Create connector that wraps around HTTP methods before 
       forwarding to actual HTTP services for communication with 
       MongoDB database rest api. Based on eve-mongodb-client-demo of Nicola.
    
    Public functions:
    
    * ``post``
    
    * ``get``
    
    * ``findID``

    """
            
    def post(self,data,resource):
        """POST bulk of list, also work with single list.
    
        Args:
            :param data(list): list of patent data that are parsed from json.
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
            
        """
        start = time.time()
        print 'Posting list of cited patents to MongoDB [ ]',
        print '\b'*3,
        sys.stdout.flush()
        dummy=[]
        count_citations = 0
        count_patents=0
        spinner = _spinning_cursor()
        if resource=="patents":
            for i in range(len(data)):
                citation_list=[]
                # Formatting numerical data to int type while checking
                data[i]["number-of-claims"]= int(data[i]["number-of-claims"])
                for item in data[i]["citations"]:
                    val= item.values()
                    citation_list.extend(val)
                    # Create dummy variable for citation ID so we can make link later
                    sys.stdout.write(spinner.next())
                    sys.stdout.flush()
                    time.sleep(0)
                    count_citations = count_citations+1
                    sys.stdout.write('\b')
                    sys.stdout.flush()
                    dummy.append({"patid":val[0]})              
                data[i]["citations"]=copy.deepcopy(citation_list)
                # Post Our Dummy patents
                p=self._post(resource,dummy)
                # Method not allowed         
                if p.status_code == 405:
                    print 'Method is not Allowed'
                else:
                    # Check if dummy is not empty, which means there is patent
                    # without citations
                    if dummy:
                        if p.status_code == 500:
                            print 'Internal Error'
                            return 1
                        elif p.json()["_status"]=='OK':
                            pass
                        else: 
                            # There were duplications in our submit
                            # Let's filter it
                            # If the error response with list of items
                            if "_items" in p.json().keys():
                                resub=self.removeDictDuplication(dummy,p.json()["_items"])
                            else:
                                s=[p.json()["_issues"]]
                                resub=self.removeDictDuplication(dummy,s)
                            # resubmit it again    
                            if resub:
                                resp=self._post(resource,resub)
                                            
        print '  \bOK] -  ', count_citations, ' cited patents in ', time.time()-start
        
        # Post Our primary patent, we also need to check
        # the existence of our actual patent generated from dummy
        # if exist, we overwrite the existing. So we will use put here instead
        # Search for existing patent and append to our new data
        start = time.time()
        print 'Posting main patents to MongoDB [ ]',
        print '\b'*3,
        sys.stdout.flush()
        for i in range(len(data)):
            count_patents = count_patents +1
            r=self.findID(resource,data[i]["patid"])
            #Found existing node
            if r.status_code == 200:
                sys.stdout.write(spinner.next())
                r = self._put(resource+"/"+r.json()["_id"],data[i],r.json()["_etag"])
            # Nothing yet, fresh insert
            else:
                resp= self._post(resource,data[i])
            sys.stdout.flush()
            time.sleep(0)
            sys.stdout.write('\b')
            sys.stdout.flush()
        print ' \bOK] - ', count_patents, ' was posted.  Completed in ',  time.time()-start
        return 0 
        
    def removeDictDuplication(self,data,error):
        exclude=[]
        for item in error:
            if "_issues" in item.keys():
                r=[]
                s= item["_issues"]["patid"]
                r.extend([w for w in re.split('\W',s) if w])
                exclude.append({"patid":r[1]})
            else:
                pass
        for item in exclude:
            if item in data:
                data.remove(item)
        #print 'exclude', exclude
        #print 'data', data
        return data
                
    
    def removeListDuplication(self,data):
        """Remove duplicated data from list.
    
        Args:
            :param data(list): list of cited patent data that are parsed from json.
    
        Returns: 
            :param r(dict): set of cited patents
            
        """
        data=list(set(data))
        keys=[]
        r=[]
        start = time.time()
        print '- Creating dictionary set of citation patent [ ]',
        print '\b'*3,
        sys.stdout.flush()
        count =0
        spinner = _spinning_cursor()
        for k in range(len(data)):
            keys.append("patid")
            r.append(dict(izip(keys,data)))
            sys.stdout.write(spinner.next())
            count = count +1
            sys.stdout.flush()
            time.sleep(0)
            sys.stdout.write('\b')
            sys.stdout.flush()
        print ' \bOK] -  ', count, ' cited patents left ', time.time()-start
        return r
    
    def get(self,resource):
        """GET an endpoint collection.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
            
        """
        r = self._get(resource)
        return r
   
    def findID(self,resource,key):
        """Return document of specific ID from a resource.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
            :param key(str): an ID of document within resource/collection.
            
        Returns: 
            :param r(dict): json object of the response
            
        """
        resource = self.endpoint(resource)+key
        r = requests.get(resource)
        return r
        
def _spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor
                    
if __name__ == '__main__':
    # Initiate Connector
    mongo_client=MongoDBConnector(ENTRY_POINT)
    data=[]
    inventors=[]
    neo_client=Neo4jDBConnector(NEO4J_DATABASE)
    #a=client.get("data")
    # Open file to read
    with open(FILE_NAME) as file:
        # Parse json file to Element Tree
        objects = ijson.items(file,'item')
        # Build up our list data to post from
        print 'Loading json ... Please wait [ ]',
        print '\b'*3,
        sys.stdout.flush()
        start=time.time()
        spinner = _spinning_cursor()
        for o in objects:
            data.append(o)
            sys.stdout.write(spinner.next())
            sys.stdout.flush()
            time.sleep(0)
            sys.stdout.write('\b')
            sys.stdout.flush()
        print ' \bOK] -  Completed in ',  time.time()-start    
        
        #neo_r = neo_client.post(data=data,resource="data/transaction",label="Patent")
        #neo_r = neo_client.post(data=data,resource="data/transaction",label="Inventor")   
        
        # Example APIs
        #di = client._delete_all("inventors")
        #mongo_dp = mongo_client._delete_all("patents")
        mongo_r = mongo_client.post(data=data,resource="patents")
                 
        #query='?where={"citations": {"$regex": ".*2003/0001416.*"}}'
        #g=client.find("patents",query)
     
     