
import re
import logging


logging.basicConfig(
    format='[%(asctime)s] %(levelname)-8s  [%(name)s] %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger('rule_parser')


delimiters_list = "(,|\\]|\\[|\\(|\\)|=|->|∞|:|{|}|#.*)"
## add > < and - to delimiters
delimiters_list = "(->|>|<|-|<=|>=|,|\\]|\\[|\\(|\\)|=|∞|:|{|}|#.*)"
delimiters_list = "(->|>|<|<=|>=|,|\\]|\\[|\\(|\\)|=|∞|:|{|}|#.*)"

def get_key_value(keys_list):
	if len(keys_list) == 3 and keys_list[1] == "=":
		key_ = keys_list [0]
		value_ = keys_list [2]
		try:
			## try convet it to int
			value_ = int(value_)
		except :
			try :
				value_ = float(value_)
			except :
				## just store it as it is
				pass
		return {key_:value_}
	else:
		print(keys_list)
		raise NotImplementedError("Attribute format not supported yet")

def fix_membrane_objects(membrane):
	membrane_objs : list = membrane['objects']
	membrane_objs.reverse()
	objs = []
	n = 1
	## TODO :: handle λ funtion in objects 
	## 
	while len(membrane_objs) > 0:
		item = membrane_objs.pop()
		if isinstance(item,int) or item == "∞" or isinstance(item,RangeOperator):
			n = item
		if isinstance(item,str) and item != "∞":
			if item == "∂" :
				membrane['action'] = item
			else :
				if isinstance(n,RangeOperator):
					## this is a range operator
					n.object = item
				objs.append({item:n})
			n = 1
	if len(objs) == 0 :
		del membrane['objects']
	else:
		membrane['objects'] = objs


def get_rule_attrs(attrs_list):
	#print(attrs_list)
	parsing_stack = []
	atts_dict = {}
	for token in attrs_list :
		if token == "," or ( token == ")" and len(parsing_stack) > 0 ) : #and not isinstance(parsing_stack[-1],list)  ):
			new_list = []
			## in case of 
			while len(parsing_stack) > 0:
				if parsing_stack[-1] == "(" or parsing_stack[-1] == "{":
					break
				stack_top = parsing_stack.pop()
				if stack_top == ":":
					# pairs
					left_pair = parsing_stack.pop()
					right_pair = new_list.pop()
					new_list.insert(0,{left_pair:right_pair})
				else :
					new_list.insert(0,stack_top)
				if len(parsing_stack) > 0 and (isinstance(parsing_stack[-1],list) or isinstance(parsing_stack[-1],dict)):
					break
			if len(new_list)==0:
				logger.warning("An empty paramaters before ,")
			## if this is mapping
			if len(new_list) == 1 and isinstance(new_list[0],dict):
				## convert to dict
				new_list = new_list[0]
			# if len(parsing_stack) > 0 and isinstance(parsing_stack[-1],dict):
			# 	parsing_stack[-1].update(new_list)
			# else:
			# 	parsing_stack.append(new_list)
			parsing_stack.append(new_list)
		if token == ",":
			pass
		elif token == "}":
			new_set = []
			while len(parsing_stack) > 0:
				stack_top  = parsing_stack.pop()
				if stack_top == "{" or isinstance(stack_top,list)  or isinstance(stack_top,dict):
					parsing_stack.append(stack_top)
					break
				if stack_top == ":":
					# pairs
					left_pair = parsing_stack.pop()
					right_pair = new_set.pop()
					new_set.insert(0,{left_pair:right_pair})
				else :
					new_set.insert(0,stack_top)
			if len(new_set) == 1 and isinstance(new_set[0],dict):
				## convert to dict
				new_set = new_set[0]
			parsing_stack.append(new_set)
			## each part here should be dict otherwise something is wrong
			if True : # stack_top == "{" :
				new_map = None			
				while len(parsing_stack) > 0:
					stack_top  = parsing_stack.pop()
					if stack_top == "{":
						parsing_stack.append(new_map)
						break
					if isinstance(stack_top,dict) :
						if new_map == None:
							new_map = {}
						if isinstance(new_map,dict):
							new_map.update(stack_top)
							#new_map.update (stack_top)
						else:
							raise ValueError("Mapping values errors, something is wrong in the provided map set")
					if isinstance(stack_top,list):
						if new_map == None:
							new_map = []
						if isinstance(new_map,list):
							new_map.extend(stack_top)
						else:
							raise ValueError("List values errors, something is wrong in the provided list item")
			if stack_top != "{":
				raise ValueError("Mapping values errors, missing encolsing { in the map")

		# elif token == ")":
		# 	while len(parsing_stack) > 0 :

		# 	while len(parsing_stack) > 0:
		# 		stack_top  = parsing_stack.pop()
		# 		if stack_top == "(":
		# 			break
		# 		if isinstance(stack_top,list):
		# 			atts_dict.update(get_key_value(stack_top))
		# 		else :
		# 			raise ValueError("Unexpected key:value pair in attributes list")
		else:
			parsing_stack.append(token)

	for value_key_pair in parsing_stack :

		if (value_key_pair != "(" and value_key_pair != ")"):
			if isinstance(value_key_pair,list):
				atts_dict.update(get_key_value(value_key_pair))
			else :
				raise ValueError("Unexpected key:value pair in attributes list")

	return atts_dict

class RangeOperator:
	def __init__(self):
		self.start = None
		self.end = None
		## define if the range include the end or not
		self.include_end = True
		## define if the range include the start or not
		self.include_start = True
		self.type = "range"
		self.object = None
	def __str__(self):
		if self.object:
			return f"R<{self.start},{self.end}>{self.object}"
		return f"R<{self.start},{self.end}>"
	def __repr__(self):
		if self.object:
			return f"R<{self.start},{self.end}>{self.object}"
		return f"R<{self.start},{self.end}>" 

def get_rule_membranes_structures(tokens):
	parsing_stack = []
	for token in tokens :
		if token == "]" and len(parsing_stack) == 0 :
			logger.error("unexpected left ] encountered")
			raise ValueError("Unexpected left ] encountered")
		# if token == "<":
		# 	## we are opening a range operator
		# 	parsing_stack.append(token)
		if token == ",":
			## just white space
			## pop last token and add it to the prevoius token or array ?
			
			## stack_top can not be [
			new_list = []
			## in case of 
			while len(parsing_stack) > 0:
				if isinstance(parsing_stack[-1],dict):
					## the last element is a membrane, so leave it for now
					break
				if isinstance(parsing_stack[-1],list):
					if len(new_list)==0:
						logger.warning("An empty paramaters before ,")
					parsing_stack[-1].extend(new_list)
					new_list.clear()
					break
				elif parsing_stack[-1] == "[" :
					#parsing_stack.append(new_list)
					break
				else:
					new_list.insert(0,parsing_stack.pop())
			if len(new_list)>0:	
				parsing_stack.append(new_list)
		elif token == "]" :
			#	pop all item from the stack until we get right [
			new_membrane = {"objects":[],"membranes":[]}
			while len(parsing_stack)>0:
				stack_top = parsing_stack.pop()
				if stack_top == "[":
					## this is the count number before the membrane
					if len(parsing_stack) > 0 and isinstance(parsing_stack[-1],int)  :
						new_membrane["number"] = parsing_stack.pop()
					fix_membrane_objects(new_membrane)
					parsing_stack.append(new_membrane)
					break
				elif isinstance(stack_top,str) or isinstance(stack_top,int) or isinstance(stack_top,RangeOperator) :
					new_membrane["objects"].insert(0,stack_top)
				elif isinstance(stack_top,list):
					stack_top.extend(new_membrane["objects"])
					new_membrane["objects"] = stack_top
				elif isinstance(stack_top,dict):
					new_membrane["membranes"].insert(0,stack_top)
			if stack_top != "[":
				print("Something is wrong")
		elif token == "[":
			# close whatever before this
			parsing_stack.append(token)
		elif isinstance(token,str) and ( len(parsing_stack) > 0 and isinstance(parsing_stack[-1],dict) ):
			## membrane name
			## end of membrane
			parsing_stack[-1]["membrane"] = token.strip()
		elif token == ">":
			## we are closing a range operator
			# range operator object
			new_range =  RangeOperator()
			while len(parsing_stack)>0:
				stack_top = parsing_stack.pop()
				if stack_top == "<":
					break
				if stack_top == ":":
					# pairs
					left_pair = parsing_stack.pop()
					if isinstance(left_pair,int):
						new_range.start = left_pair
					elif isinstance(left_pair,str) and left_pair == "<":
						break
				elif isinstance(stack_top,int) or stack_top == "∞":
					if new_range.end == None:
						new_range.end = stack_top
					else:
						raise ValueError("Unexpected number in the range operator")
			if stack_top != "<":
				print("Something is wrong")
				raise ValueError("Unexpected > encountered in the range operator")
			else:
				parsing_stack.append(new_range)
		else:
			parsing_stack.append(token)

	outside_objects = []
	for elem in parsing_stack :
		if isinstance(elem,list):
			outside_objects.extend(elem)
	if len(outside_objects) > 0 :
		new_membrane = {"objects":outside_objects,"membranes":[]}
		for elem in parsing_stack :
			if isinstance(elem,dict):
				new_membrane["membranes"].append(elem)
		fix_membrane_objects(new_membrane)
		return new_membrane
	return parsing_stack



def get_membranes_structures(tokens):
	parsing_stack = []
	for token in tokens :
		if token == "]" and len(parsing_stack) == 0 :
			logger.error("unexpected left ] encountered")
			raise ValueError("Unexpected left ] encountered")
		if token == ",":
			## just white space
			## pop last token and add it to the prevoius token or array ?
			
			## stack_top can not be [
			new_list = []
			## in case of 
			while len(parsing_stack) > 0:
				if isinstance(parsing_stack[-1],dict):
					## the last element is a membrane, so leave it for now
					break
				if isinstance(parsing_stack[-1],list):
					if len(new_list)==0:
						logger.warning("An empty paramaters before ,")
					parsing_stack[-1].extend(new_list)
					new_list.clear()
					break
				elif parsing_stack[-1] == "[" :
					#parsing_stack.append(new_list)
					break
				else:
					new_list.insert(0,parsing_stack.pop())
			if len(new_list)>0:	
				parsing_stack.append(new_list)
		elif token == "]" :
			#	pop all item from the stack until we get right [
			new_membrane = {"objects":[],"membranes":[]}
			while len(parsing_stack)>0:
				stack_top = parsing_stack.pop()
				if stack_top == "[":
					if len(parsing_stack) > 0 and isinstance(parsing_stack[-1],int)  :
						new_membrane["number"] = parsing_stack.pop()
					fix_membrane_objects(new_membrane)
					parsing_stack.append(new_membrane)
					break
				elif isinstance(stack_top,str) or isinstance(stack_top,int) :
					new_membrane["objects"].insert(0,stack_top)
				elif isinstance(stack_top,list):
					stack_top.extend(new_membrane["objects"])
					new_membrane["objects"] = stack_top
				elif isinstance(stack_top,dict):
					new_membrane["membranes"].insert(0,stack_top)
			if stack_top != "[":
				print("Something is wrong")
		elif token == "[":
			# close whatever before this
			parsing_stack.append(token)
		elif isinstance(token,str) and ( len(parsing_stack) > 0 and isinstance(parsing_stack[-1],dict) ):
			## membrane name
			## end of membrane
			parsing_stack[-1]["membrane"] = token.strip()
		else:
			parsing_stack.append(token)

	outside_objects = []
	for elem in parsing_stack :
		if isinstance(elem,list):
			outside_objects.extend(elem)
	if len(outside_objects) > 0 :
		new_membrane = {"objects":outside_objects,"membranes":[]}
		for elem in parsing_stack :
			if isinstance(elem,dict):
				new_membrane["membranes"].append(elem)
		fix_membrane_objects(new_membrane)
		return new_membrane
	return parsing_stack

def object_name_tokenizer(object):
	"""
	numberObjectName
	remove digits from the start of the name if  
	"""
	if len(object) <= 1 :
		return [object]
	if object[0].isdigit():
		for i in range(len(object)):
			if not object[i].isdigit():
				break
		if i == len(object)-1 and object[-1].isdigit() :
			return [object]
		return [object[0:i],object[i:]]
	else:
		return [object]

# Split a string if it contains any of the specified patterns: "condition :", "cond:", "conditions :", or "condition    :"
def split_condition_string(input_str):
	"""
	Split the input string based on specific patterns like "condition :", "cond:", etc.
	:param input_str: The input string to be split.
	:return: A list of split strings.
	"""
	split_pattern = re.compile(r'condition\s*:|cond\s*:|conditions\s*:')
	return [s.strip() for s in split_pattern.split(input_str) if s.strip()]


def get_rule(rule_line):
	"""
		each line is rule , we should keep it simple
	"""

	## split the rule if it contains condition
	## the condition is the part after the condition keyword
	condition_str = None
	split_condition_strings = split_condition_string(rule_line)
	if len(split_condition_strings) > 1:
		rule_line = split_condition_strings[0]
		condition_str = split_condition_strings[1]
		# logger.debug(f"Rule with condition : {rule_line}")
		# logger.debug(f"Condition : {condition_str}")

	tokens  = re.split(delimiters_list, rule_line)
	# rule has three parts
	## right_hand_side -> left_hand_side rule_attrs
	## rule_attrs format (att_key=att_value,....)
	rhs = []
	lhs = []
	atts_side = []
	line_ending = []
	i=0   ### i add this because it hives error with the new scenarion the is refrenced before assigned
	
	## TODO :: handle multiple () in this part with a stack 
    
	for i in range(len(tokens)-1,0,-1):
		token = tokens[i]
		token = token.strip()
		if token == "":
			continue
		if token == ")":
			## end of attr_part
			atts_side.insert(0,token)
		else :
			if len(atts_side) == 0 : # did not started yet
				line_ending.append(token)
			else: 
				atts_side.insert(0,token)

		if token == "(":
			## start of atts part
			break
	lhs_end = i - 1
	if len(atts_side) == 0:
		lhs_end = len(tokens)-1
	# logger.debug(f"rule_attrs ended at {i} token")
	for i in range(0,lhs_end+1):
		token = tokens[i]
		token = token.strip()
		if token == "" or token.startswith("#"):
			continue
		if token == "->":
			## stop here
			break
		## 
		tks = token.split(" ")
		if len(tks ) == 1 :
			tks = object_name_tokenizer(token)
		if len(tks) > 1 :
			rhs.extend(tks)
		else:
			rhs.append(token)
	lhs_start = i + 1
	for i in range(lhs_start,lhs_end+1):
		token = tokens[i]
		token = token.strip()
		if token == "" or token.startswith("#"):
			continue
		tks = token.split(" ")
		if len(tks ) == 1 :
			tks = object_name_tokenizer(token)
		if len(tks) > 1 :
			lhs.extend(tks)
		else:
			lhs.append(token)
	
	logger.debug(f"Rule attrs : {''.join(atts_side)}")
	logger.debug(f"Rule rhs : {''.join(rhs)}")
	logger.debug(f"Rule lhs : {''.join(lhs)}")
	for i in range(len(rhs)):
		token = rhs[i]
		try :
			token_num	= int(token)
			rhs[i] = token_num
		except :
			pass
	for i in range(len(lhs)):
		token = lhs[i]
		try :
			token_num	= int(token)
			lhs[i] = token_num
		except :
			pass
	
	input_str = get_rule_membranes_structures(rhs)
	output_str = get_membranes_structures(lhs)
	rule_atts = get_rule_attrs(atts_side)


	if  isinstance(output_str,list) and len(output_str) == 1 and isinstance(output_str[0],str) and output_str[0]== "∂": 
		# input_str[0]["membrane"]
		## otherwise fail
		output_str[0] = {"membrane":input_str[0]["membrane"],"action": "∂"}

	if not "membrane"  in rule_atts :
		if len(input_str) == 1 and  len(output_str) == 1 :
			rule_atts["membrane"] = input_str[0]["membrane"]
			#adjust_rule_1(input_str)
			if output_str[0]["membrane"] != input_str[0]["membrane"]:
				logger.warning(f"input and output membrane are differnt in rule :{rule_atts}" )
		elif len(input_str) == 1:
			rule_atts["membrane"] = input_str[0]["membrane"]
			logger.warning(f"Ambiguity detecting container membrane of the rule  :{rule_atts}" )
		else:
			logger.warning(f"Can not detect container membrane of the rule :{rule_atts}" )
	if len(input_str) == 1:
		input_str = input_str[0]
	elif len(input_str) > 1 :
		input_str = input_str
	else:
		logger.warning(f"No input in rule :{rule_atts}" )
	if len(output_str) > 1 :
		output_str = output_str
	elif len(output_str) == 1 :
		output_str = output_str[0]
	else :
		logger.warning(f"No ouput in rule :{rule_atts}" )

	rule_atts["input"] = input_str
	rule_atts["output"] = output_str

	if condition_str:

		rule_atts["condition"] = condition_str

	return rule_atts

def membranes_to_list_objects(rule_part):
	if 'membranes' in rule_part:
		membranes_list = rule_part['membranes']
		new_membranes_list = []
		for membrane in membranes_list:
			membrane_name = membrane["membrane"]
			del membrane["membrane"]
			membrane = membranes_to_list_objects(membrane)
			if membrane :
				new_membranes_list.append({membrane_name:membrane} )
			else:
				new_membranes_list.append(membrane_name)
			
		rule_part['membranes'] = new_membranes_list
		if len(new_membranes_list) == 0:
			del rule_part['membranes'] 
	if len(rule_part) == 0 :
		return None
	if len(rule_part)==1 and 'number' in rule_part:
		return rule_part['number']
	if len(rule_part)==1 and 'action' in rule_part:
		return rule_part['action']
	return rule_part

def adjust_rule_input(new_rule):
	## we need to adjust the input 
	## input must be explicit and container membrane is mentioned in the membrane list 

	part = "input"
	input_part  = new_rule[part]
	## input part 
	membrane_name = ""
	if 'membrane' in new_rule: ## then we have it 
		rule_membrane_name = new_rule['membrane']
	
	if isinstance(input_part,dict): ## this is the container membrane
		## however this come from outsite which we arealy know
		if 'membrane' in input_part :
			input_membrane_name =  input_part["membrane"]
			del input_part["membrane"]
			input_part = membranes_to_list_objects(input_part)
			if input_part :
				new_rule[part] = {"membranes":[{input_membrane_name:input_part}]}
			else:
				new_rule[part] = {"membranes":[input_membrane_name]}
				
				
		else:
			## we will depend on tha fact that the membranes list has the correct membrane
			input_part = membranes_to_list_objects(input_part)
			new_rule[part] = input_part

	if isinstance(input_part,list):
		new_membranes_list = []
		for membrane in input_part:
			membrane_name = membrane["membrane"]
			del membrane["membrane"]
			membrane = membranes_to_list_objects(membrane)
			if membrane:
				new_membranes_list.append({membrane_name:membrane} )
			else :
				new_membranes_list.append(membrane_name )
		new_rule[part] = {"membranes":new_membranes_list}


def adjust_rule_output(new_rule):
	## we need to adjustthe output Membrane part

	part="output"
	## input part 
	rule_membrane_name = ""
	if 'membrane' in new_rule:
		rule_membrane_name = new_rule['membrane']
	input_part  = new_rule[part]
	if isinstance(input_part,dict): ## one membrane
		
		if 'membrane' in input_part :
			input_membrane_name =  input_part["membrane"]
			del input_part["membrane"]
			input_part = membranes_to_list_objects(input_part)
			if input_part :
				new_rule[part] = {"membranes":[{input_membrane_name:input_part}]}
			else:
				new_rule[part] = {"membranes":[input_membrane_name]}
		else:
			input_part = membranes_to_list_objects(input_part)
			new_rule[part] = input_part

	if isinstance(input_part,list):
		new_membranes_list = []
		for membrane in input_part:
			membrane_name = membrane["membrane"]
			del membrane["membrane"]
			membrane = membranes_to_list_objects(membrane)
			if membrane:
				new_membranes_list.append({membrane_name:membrane} )
			else :
				new_membranes_list.append(membrane_name )
		new_rule[part] = {"membranes":new_membranes_list}
		
	# else :
	# 	import copy
	# 	if isinstance(input_part,list):
	# 		input_part_d = {"membranes":copy.deepcopy( input_part)}
	# 		input_part_d = membranes_to_list_objects(input_part_d)
	# 		new_rule[part] = input_part_d

def adjust_rule_objects(new_rule, membrane = None, membrane_fcmn = ""):
	if not membrane: 
		if "input" in new_rule:
			membranes = new_rule["input"]["membranes"]
			for child_membrane in membranes:
				adjust_rule_objects(new_rule, child_membrane)
		if "output" in new_rule:
			membranes = new_rule["output"]["membranes"]
			for child_membrane in membranes:
				adjust_rule_objects(new_rule, child_membrane)
		return
	## membrane is a dict with {membrane_name:membrane_dict}
	## get the membrane name
	if isinstance(membrane,str):
		## nothing to do
		return
	membrane_name = list(membrane.keys())[0]
	if membrane_fcmn == "":
		membrane_fcmn = membrane_name
	else:
		membrane_fcmn = f"{membrane_fcmn}.{membrane_name}"
	membrane = membrane[membrane_name]
	if not isinstance(membrane,dict): 
		return
	if "objects" in membrane:
		for obj in membrane["objects"]:
			## obj is a dict with {obj_name:obj_value}
			## obj_value is either a number or a range operator
			## get the object name
			obj_name = list(obj.keys())[0]
			## if obj_name endwith ` then it is a catalyst object
			obj_value = obj[obj_name]
			if isinstance(obj_value,RangeOperator):
				## replace the range operator with dict representation
				obj_value = obj_value.__dict__
				obj[obj_name] = obj_value
			if obj_name.endswith("`"):
				## remove it for the obj dict to add it with new name
				del obj[obj_name]
				## add the catalyst attribute to the object
				if isinstance(obj_value,dict):
					obj_value["catalyst"] = True
				elif isinstance(obj_value,int):
					obj_value = {"number":obj_value,"catalyst":True}
				else:
					raise ValueError("Catalyst object value must be either int or dict")
				## double `` is used to indicate absolue catalyst object
				if obj_name.endswith("``"):
					## remove the last two characters
					obj_name = obj_name[:-2]
					obj_value['absolute'] = True
				else:
					obj_name = obj_name[:-1]
					obj_value['absolute'] = False
				obj_value['object'] = obj_name
				obj[obj_name] = obj_value
				## add the name to the catalyst list
				if not "catalysts" in new_rule:
					new_rule["catalysts"] = []
				new_rule["catalysts"].append(f"{membrane_fcmn}.{obj_name}")
			if obj_name.startswith("Δ") :
				## delete change
				## remove Δ from the name
				del obj[obj_name]
				obj_name = obj_name[1:]
				
				if isinstance(obj_value,dict):
					obj_value["delta_change"] = True
				else:
					obj_value = {"number":obj_value,"delta_change":True}
				obj[obj_name] = obj_value

	if "membranes" in membrane:
		for child_membrane in membrane["membranes"]:
			adjust_rule_objects(new_rule, child_membrane,membrane_fcmn)
	pass



def get_membranes(membranes_section):
	"""
		each line is rule , we should keep it simple
	"""
	tokens  = re.split(delimiters_list, membranes_section)
	# membrane has one part
	## similar to right_hand_side of the rule
	rhs = []


	# logger.debug(f"rule_attrs ended at {i} token")
	for i in range(0,len(tokens)):
		token = tokens[i]
		token = token.strip()
		if token == "" or token.startswith("#"):
			continue
		## 
		tks = token.split(" ")
		if len(tks ) == 1 :
			tks = object_name_tokenizer(token)
		if len(tks) > 1 :
			rhs.extend(tks)
		else:
			rhs.append(token)
	

	for i in range(len(rhs)):
		token = rhs[i]
		try :
			token_num	= int(token)
			rhs[i] = token_num
		except :
			pass
	
	
	all_membranes = get_membranes_structures(rhs)
	return all_membranes


import os 
def parse_ini_to_yml(input_filename, output_filename ):
	dirname = os.path.dirname(input_filename)
	input_filebasename = os.path.splitext(os.path.basename(input_filename))[0]


	with open(input_filename) as f:
		line_i = 0

		rule_list = []

		collect_yaml = False
		parsing_rules = False
		parsing_membranes = False
		rules_set = {}
		comments_stack=[]
		membrances_lines=[]
		yaml_lines = ""
		system_skin = None
		while True:
			org_line = f.readline()
			if not org_line:
				break
			line = org_line.strip()
			line_i +=1
			try :
				if line.startswith("#YAML"):
					collect_yaml = not collect_yaml
					if collect_yaml:
						parsing_rules = False
						parsing_membranes = False
					continue
				if collect_yaml:
					yaml_lines += org_line
					continue

				if line.startswith("#") :
					comments_stack.append(line)
					continue
				if line == "" :
					continue
				if line.startswith("skin"):
					tokens = line.split(":")
					if len(tokens) == 2 :
						skin_key = tokens[0].strip()
						
						skin_value = tokens[1].strip()
						if skin_key == "skin" :
							system_skin = skin_value



				if line == "membranes:":
					parsing_membranes=True
					parsing_rules=False
					continue
				if line== "rules:":
					parsing_rules =True
					parsing_membranes=False
					continue
				
				if parsing_rules :
					re.split('(,|\\]|\\[|\\(|\\)|=|->)', line)
					logger.info("Parsing Rule : " + line)
					
					## you can store comments also from comments_stack
					new_rule = get_rule(line)
					comments_stack.clear()

					if "Name" in new_rule:
						rule_name = new_rule['Name'] 
						del new_rule['Name']
					else:
						rule_name = f"rule_{len(rule_list)}"
					parts = rule_name.split(".")
					adjust_rule_input(new_rule)#'input')
					adjust_rule_output(new_rule)
					adjust_rule_objects(new_rule)
					if len(parts) == 2:
						base_name = parts[0]
						if not base_name in rules_set:
							rules_set[base_name] = {base_name:[]}
							
							rule_list.append(rules_set[base_name])
						rules_set[base_name][base_name].append(new_rule)
					else :
						rules_set[rule_name] = {rule_name:new_rule}
						rule_list.append(rules_set[rule_name])
				if parsing_membranes:
					membrances_lines.extend(comments_stack)
					membrances_lines.append(line)
					comments_stack.clear()
					pass

			except Exception as ex:
				logger.error(f"Error parsing line:{line_i} {ex}")
				raise ex
			#print(line.strip())

	membrances_def = get_membranes("\n".join(membrances_lines))
	membrances_def = membranes_to_list_objects({"membranes":membrances_def})

	## remove redundant 
	mem_keys = set()
	for mem_def in list(membrances_def["membranes"]):
		if isinstance(mem_def,dict):
			mem_key = list(mem_def.keys())[0]
			pass
		else:
			mem_key = mem_def
		if mem_key in mem_keys:
			membrances_def["membranes"].remove(mem_def)
		else:
			mem_keys.add(mem_key)

	import yaml
	if yaml_lines :
		system_def = yaml.safe_load(yaml_lines)
	else :
		system_def = {"system": {}}
	if system_skin :
		system_def["system"]["skin"] = [system_skin]

	system_def["system"].update(membrances_def)
	system_def["system"]["rules"] = rule_list 

	yaml.dump(system_def, 
				open(output_filename,"w"), 
				default_flow_style=False , 
				allow_unicode=True,sort_keys=False)
	return output_filename