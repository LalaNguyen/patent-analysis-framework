"""
    mongodb-client
    ~~~~~~~~~~~~~~~
    Based on eve-mongodb-client-demo of Nicola, provides more functions to work with
    specific xml 4.5 DTD of US patents. 

"""
from eve import Eve
import requests
import json
import settings
import ijson
import copy
from itertools import izip
import time, sys

ENTRY_POINT = 'http://localhost:5000'
FILE_NAME ="data.json"   

class HTTPService(object):
    
    def __init__(self,entry):
        self.entry_point=entry
        
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
        
    def _get(self,resource):
        """Perform the actual GET.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
        """
        r = requests.get(self.endpoint(resource))
        return r.json()
        
    def _find(self,resource,query):
        resource = self.entry_point+'/'+resource+query
        r = requests.get(resource)
        return r.json()
    
               
class MongoDBConnector(HTTPService):
    """Create connector that wraps around HTTP methods before 
       forwarding to actual HTTP services for communication with 
       different database rest api.
    
    Public functions:
    
    * ``post``
    
    * ``get``
    
    * ``findID``

    """
    
    
    def __init__(self,entry):
        self.entry_point=entry
        
        
    def post(self,data,resource):
        """POST bulk of list, also work with single list.
    
        Args:
            :param data(list): list of patent data that are parsed from json.
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
            
        """
        new_data=[]
        start = time.time()
        count =0 
        print 'Checking duplicated cited patents [ ]',
        print '\b'*3,
        sys.stdout.flush()
        spinner = _spinning_cursor()
        if resource=="patents":
            dummy=[]          
            for i in range(len(data)):
                citation_list=[]
                
                for item in data[i]["citations"]:
                    val= item.values()
                    citation_list.extend(val)
                    # Create dummy variable for citation ID so we can make link later
                    # Check if the patent is already exist
                    r = self.findID(resource=resource,patid=val[0])
                    # If found
                    sys.stdout.write(spinner.next())
                    count = count +1
                    sys.stdout.flush()
                    time.sleep(0)
                    sys.stdout.write('\b')
                    sys.stdout.flush()
                    if r.status_code == 200:
                        pass
                    else:
                        #Not exist, We create new dummy document
                        dummy.append(val[0])                
                
                data[i]["citations"]=copy.deepcopy(citation_list)
        
        print ' \bOK] -  ', count, ' cited patents in ', time.time()-start
        start = time.time()        
        print '- Posting to DB server [ ]',
        print '\b'*3,
        
        spinner = _spinning_cursor()
        # Post Our Dummy patents
        if dummy:
            # remove duplicated value
            b=self.removeDuplication(dummy)
            p=self._post(resource,b)
        print '\bOK] -  Completed in ',  time.time()-start
        
        start = time.time()
        
        # Post Our primary patent, we also need to check
        # the existence of our actual patent generated from dummy
        # if exist, we remove the existing. So we will use put here instead
        # Search for existing patent and append to our new data
        print 'Checking duplicated main patents [ ]',
        print '\b'*3,
        sys.stdout.flush()
        for i in range(len(data)):
            resp = self.findID(resource=resource,patid=data[i]["patid"])
            # Not found
            sys.stdout.write(spinner.next())
            count = count +1
            sys.stdout.flush()
            time.sleep(0)
            sys.stdout.write('\b')
            sys.stdout.flush()
            if resp.status_code==404: 
                new_data.append(data[i])
            else:
                pass
        print ' \bOK] -  Completed in ',  time.time()-start
        start = time.time()
        print '- Posting to DB server [ ]',
        print '\b'*3,
        spinner = _spinning_cursor()
        valids = []
        if new_data:
            r = self._post(resource,new_data)
            if r.status_code == 201:
                response = r.json()
                if response['_status'] == 'OK':
                    for person in response['_items']:
                        if person['_status'] == "OK":
                            valids.append(person['_id'])
            else: 
                print r.json()
        print '\bOK] -  Completed in ',  time.time()-start
        return valids 
         
    def removeDuplication(self,data):
        """Remove duplicated data from list.
    
        Args:
            :param data(list): list of cited patent data that are parsed from json.
    
        Returns: 
            :param r(dict): set of cited patents
            
        """
        data=list(set(data))
        keys=[]
        r=[]
        for k in range(len(data)):
            keys.append("patid")
            r.append(dict(izip(keys,data)))
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
    client=MongoDBConnector(ENTRY_POINT)
    data=[]
    inventors=[]
    # Open file to read
    with open(FILE_NAME) as file:
        # Parse json file to Element Tree
        objects = ijson.items(file,'item')
        # Build up our list data to post from
        for o in objects:
            data.append(o)
            inventors.extend(o["inventors"])
            
        # Example APIs
        #di = client._delete_all("inventors")
        #dp = client._delete_all("patents")
        
            
        r = client.post(data=data,resource="patents")

         
        #i = client.post(data=inventors,resource="inventors")
        query='?where={"citations": {"$regex": ".*2003/0001416.*"}}'
        #g=client.find("patents",query)
     