from collections import OrderedDict
import json
from time import time

class MsgObj():
    """
	Each MsgObj contains one BSM message
	Object variables:
		id        - id of the object
		active    - Active flag. Only active objects are being sent to clients.
		            When the object is sent, the flag is being set to False. The
				    next update resets the flag to True
		lastRead  - the last time when the object was sent
		timestamp - object's timestamp
		msg       - the BSM message in json format
	"""
    def __init__(self, obj_id, timestamp, msg, active = True, lastRead = 0):
        self.id = obj_id,
        self.active = active # Only active objects are being sent
        self.lastRead = lastRead # When the object was read last time
        self.timestamp = timestamp
        self.msg = msg

    def dumpObj(self):
        print ('Id: {}, Active: {}, Last Read: {}, Timestamp: {}\nMsg: {}'.format(
			self.id, self.active, self.lastRead, self.timestamp, self.msg))
        
        
class MsgObjects():
    """
	Class that manages the Message Objects. The main methods of this class are:
	push_object - receives the BSM(s) (usually from detaction and tracking system)
	pull_object - receives request and sends the BSM (usually to Cohda)
	get_bsms    - returns all the BSMs (usually used by an externall app)
	Object variables:
	    obj_lifetime - lifetime of an object (default = 20)
		objects - OrderedDict({
		              id : MsgObj
		              .......
				  })
	              where id is an object id and MsgObj is an instance of MsgObj class
	"""			  
	
    def __init__(self, obj_lifetime = 20):
        self.objects = OrderedDict()
        self.obj_lifetime = obj_lifetime
    
    def first(self):
        if len(self.objects) == 0:
            return None
        return next(self.objects)
    
    def sort_objects(self):
        self.objects = OrderedDict(sorted(
            self.objects.items(), key=lambda item: item[1].lastRead))
        
    def push_object(self, msg, force_sort = False):
        if isinstance(msg, str):
            msg_dict = json.loads(msg)
        elif isinstance(msg, dict):
            msg_dict = msg
            msg = json.dumps(msg_dict)
            
        if 'id' in msg_dict:
            objid = msg_dict['id']
            if 'secMark' in msg_dict:
                timestamp = msg_dict['secMark']
            else:
                timestamp = time()
            if objid in self.objects.keys():
                self.objects[objid].msg = msg
                self.objects[objid].timestamp = timestamp
                self.objects[objid].active = True
            else:
                obj = MsgObj(objid, timestamp, msg)
                self.objects[obj.id] = obj
        else:
            return 1 # Error - cannot push the object
        
        if force_sort:
            self.sort_objects()
        return 0

    def pull_object(self, force_sort = False):
        if len(self.objects) == 0:
            return None
        if force_sort:
            self.sort_objects()
        key, obj = self.objects.popitem(last = False)
        
        # Recurrence. If our object is too old, let's take the next one. 
        # Current object is already removed from the list by popitem
        if time() - obj.timestamp > self.obj_lifetime:
            return (self.pull_object(False))
        
        
        self.objects[key] = obj
        if not obj.active:
            return None
        obj.lastRead = time()
        obj.active = False
        return obj
    
    
    def pull_objects(force_sort = False):
        if force_sort:
            self.sort_objects()
        ret = copy.deepcopy(self.objects)
        self.objects = OrderedDict()
        return ret
    
    def pull_bsm(self, force_sort = False):
        obj = self.pull_object(force_sort)
        if obj is None:
            return '{"msg" : ""}'
        return obj.msg
    
    def get_bsms(self, last_updated = None, force_sort = False):
        """
        Returns bsm msgs for all objects
        Arguments: 
            last_updated - if not None (int/float) returns only the objects updated
                           in last last_updated seconds
            force_sort   - if true, then objects are sorted first (default = False)
        Returns:   list with bsm msgs in json format
        """
        if force_sort:
            self.sort_objects()
        if last_updated is not None:
            return [x.msg for x in self.objects.values() if time() - x.timestamp < last_updated]
        return [x.msg for x in self.objects.values()]
        
    