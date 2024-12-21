## DEFINE gloabl here
##################
import random
import string
from operator import itemgetter, attrgetter
from typing import List


PROPERTY_MEMBRANES = "membranes"
PROPERTY_INPUT='input'
PROPERTY_OUTPUT='output'
PROPERTY_FROM_MAPPING='copy_from'
PROPERTY_NAME="name"
PROPERTY_PARENT="parent"
PROPERTY_FCMN="fcmn"
PROPERTY_LEVEL="level"
PROPERTY_PERSONS_POPULATION_PERCENTAGE= 'PPP'
PROPERTY_INPUT_POPULATION_PERCENTAGE= 'IPP'
PROPERTY_RULE_PRIORITY= 'RPI'
PROPERTY_RULE_PERCENTAGE='RPR'
PROPERTY_ACTION="action"
PROPERTY_TYPE="type"
PROPERTY_FORMAT="format"
PROPERTY_MEMBRANE = "membrane"
PROPERTY_RULE='rule'
PROPERTY_PROCESS='process'
PROPERTY_CATALYSTS='catalysts'
PROPERTY_CATALYST='catalyst'
PROPERTY_CONDITION='condition'
PROPERTY_TIME='time'
PROPERTY_RULES='rules'
PROPERTY_OBJECTS="objects"
PROPERTY_SKIN="skin"
PROPERTY_N="number"

list_symbols=['∂','λ']
DISSOLVE_ACTION='dissolve'
CREATE_ACTION='create'
CLONE_ACTION='clone' ## this is rename RENAME_ACTION
RENAME_ACTION='rename'
MOVE_ACTION='move'
ERASING_ACTION = "erase"
DISSOLVE_ACTION_SYMBOL='∂'
ERASING_OUTPUT_SYMBOL = 'λ'

INF_SYMBOL =  "∞"


RULE_DEFAULT_PPP = 1.0
# INPUT_POPULATION_PERCENTAGE 0-1
# default 100%
RULE_DEFAULT_IPP = 1.0
# RULE_PRIORITY
# default 1, all 1 eqaul priority
RULE_DEFAULT_RPI = 1
# RULE_PERCENTAGE probability
# default 100%
RULE_DEFAULT_RPR = 1.0
RULE_DEFAULT_NAME = "rule"
##
INPUT_FORMAT_V1 = "v1"

### other keys
K_MAP_ENTRY = 'map_entry'
K_MOVING_COUNT = 'moving_count'
K_OUTPUT_COUNT = 'output_count'
K_SOURCE_MAPPING = 'source_mapping'
K_TOTAL_NUMBER = "total_number"
K_OUTPUT_MEMBRANES= "output_membranes"
K_TOTAL_OUTPUT_COUNT = 'total_output_count'


RULE_PROPERTY_SET = set([PROPERTY_INPUT,PROPERTY_OUTPUT,
						PROPERTY_PERSONS_POPULATION_PERCENTAGE,
						PROPERTY_INPUT_POPULATION_PERCENTAGE,
						PROPERTY_RULE_PERCENTAGE,
						PROPERTY_RULE_PRIORITY,
						PROPERTY_NAME,
						PROPERTY_RULE,
						PROPERTY_MEMBRANE,
						PROPERTY_FROM_MAPPING,
						PROPERTY_TIME,
						PROPERTY_PROCESS,
						PROPERTY_CATALYSTS,
						PROPERTY_CONDITION])


TIME_UNIT_HOUR = "h"
TIME_UNIT_SECOND = "s"
TIME_UNIT_MINUTE = "m"
TIME_UNIT_DAY = "d"
TIME_UNIT_WEEK = "w"


##################
class InValidFormat(Exception):
	pass

UNRESOLVED_MAPPED_VALUE = "__"
def unpackList(dict_list : list, pack_dick_key = "_id_" , unique_keys = True):
	'''
		dict_list is a list of named dict normally loadded from yaml file
		[{"name1":{....}},[{"name2":{....}}]]
		the return is a list in each elem is replaced with a a dict object with one elem
		[{"_id_":"name1",....},[{"_id_":"name2",....}]]

		function modify dict_list directly
		TODO unique_keys options is not implemented  
	'''
	## TODO :: 
	for i in range(len(dict_list)): 
		dict_obj = dict_list[i]
		if isinstance(dict_obj,str) :
			## a simple string is a key with not dict values to add
			dict_list[i] = {pack_dick_key:dict_obj}

		else :
			if(len(dict_obj) > 1):
				raise ValueError(f"dict obj {i} in unpackList contains more than one item.")
			dict_obj_key = (list((dict_obj.keys())))[0]
			dict_obj_value = dict_obj[dict_obj_key]
			if not isinstance(dict_obj_value,dict) :
				dict_obj_value = {UNRESOLVED_MAPPED_VALUE:dict_obj_value}
			dict_obj_value[pack_dick_key] = dict_obj_key
			## substitute with new value
			dict_list[i] = dict_obj_value
	#return dict_list

def unpackListAsDict(dict_list : list, pack_dick_key = None ):
	'''
		similar to unpackList but the return is a straight dict of object hashed with pack_dick_key 
		dict_list is a list of named dict normally loadded from yaml file
		[{"name1":{....}},[{"name2":{....}}]]
		the return is a list in each elem is replaced with a a dict object with one elem
		{
			"name1" : {"_id_":"name1",....},
			"name2" : {"_id_":"name2",....}
		}
	'''
	dict_hash = dict()
	for i in range(len(dict_list)): 
		dict_obj = dict_list[i]
		if isinstance(dict_obj,str) :
			## a simple string is a key with not dict values to add
			dict_hash[dict_obj] = {}
			if pack_dick_key :
				dict_hash[dict_obj][pack_dick_key] = dict_obj
		else :
			if(len(dict_obj) > 1):
				raise ValueError(f"dict obj {i} in unpackList contains more than one item.")
			dict_obj_key = (list((dict_obj.keys())))[0]
			dict_obj_value = dict_obj[dict_obj_key]
			if pack_dick_key :
				dict_obj_value[pack_dick_key] = dict_obj_key
			## substitute with new value
			if dict_obj_key in dict_hash :
				if isinstance(dict_hash[dict_obj_key],int) and isinstance(dict_obj_value,int):
					## just increment it
					dict_obj_value += dict_hash[dict_obj_key]
				else :
					raise ValueError(f"unpackListAsDict duplicate key:{dict_obj_key} found in provided list")
			dict_hash[dict_obj_key] = dict_obj_value
	return dict_hash


def hash_list(list_objs,hash_key):
	'''
		take a list of dict objects and retrun and index hash of it
		each object must contains hash_key 
	'''
	dict_hash = {}
	for i in range(len(list_objs)):
		dict_hash[list_objs[i][hash_key]] = i
	return dict_hash


def unresolved_value_to_dict(unresolved_value):
	"""
		fix yaml struture in case a map list is provided in for objects or membrane
		- object_value : custom_value

		- o : 100
		- o : action
		- m : 10
		- m : action

		Return dict with the actual key value mapping 
	"""
	if isinstance(unresolved_value,str) and unresolved_value == INF_SYMBOL:
		return {PROPERTY_N:INF_SYMBOL}
	if isinstance(unresolved_value,int):
		return {PROPERTY_N:unresolved_value}
	if unresolved_value == DISSOLVE_ACTION or  unresolved_value == DISSOLVE_ACTION_SYMBOL:
		return {PROPERTY_ACTION:DISSOLVE_ACTION}
	return None

def get_random_string(length):
    # choose from all lowercase letter
	letters = string.ascii_lowercase
	result_str = ''.join(random.choice(letters) for i in range(length))
	return result_str


def multisort(xs : List, specs):
	for key, reverse in reversed(specs):
		xs.sort(key= attrgetter(key), reverse=reverse)
	return xs

def is_integer_num(n):
    if isinstance(n, int):
        return True
    if isinstance(n, float):
        return n.is_integer()
    return False

def get_time(str_time : str):
	time_unit = ""
	time = ""
	str_time = str_time.lower()
	if str_time.endswith(TIME_UNIT_MINUTE) :
		time_unit = TIME_UNIT_MINUTE
	elif str_time.endswith(TIME_UNIT_HOUR):
		time_unit = TIME_UNIT_HOUR
	elif str_time.endswith(TIME_UNIT_SECOND):
		time_unit = TIME_UNIT_SECOND
	elif str_time.endswith(TIME_UNIT_DAY):
		time_unit = TIME_UNIT_DAY
	elif str_time.endswith(TIME_UNIT_WEEK):
		time_unit = TIME_UNIT_WEEK
	str_time = str_time[:-1]
	time = float(str_time)
	return time,time_unit

## take a string of the format
# r.0
# r.1 
# X.1
# y.2
# and cut it to two parts
# name and name_group
def get_rule_name_group(rule_name):
	
	tokens = rule_name.split(".")
	# if there are two tokens
	if len(tokens) == 2:
		name_group = tokens[0]
	else:
		name_group = None
	return name_group


#
