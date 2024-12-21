import math
from typing import Dict, List, Set
from .helper import *
import logging
from colorama import Fore as Fore_org
import copy
import random
from sortedcontainers import SortedList
from collections import deque 
import os
import yaml
########################################
compress_membranes = True
is_debug= False
use_colores = True
Fore = copy.copy(Fore_org)
if not use_colores:
	Fore.BLACK           = ""
	Fore.RED             = ""
	Fore.GREEN           = ""	
	Fore.YELLOW          = ""
	Fore.BLUE            = ""
	Fore.MAGENTA         = ""	
	Fore.CYAN            = ""	
	Fore.WHITE           = ""
	Fore.RESET           = ""

  # These are fairly well supported, but not part of the standard.
	Fore.LIGHTBLACK_EX   = ""
	Fore.LIGHTRED_EX     = ""
	Fore.LIGHTGREEN_EX   = ""
	Fore.LIGHTYELLOW_EX  = ""
	Fore.LIGHTBLUE_EX    = ""
	Fore.LIGHTMAGENTA_EX = ""
	Fore.LIGHTCYAN_EX    = ""
	Fore.LIGHTWHITE_EX   = ""
def use_color(use_colores):
	Fore = copy.copy(Fore_org)
	if not use_colores:
		Fore.BLACK           = ""
		Fore.RED             = ""
		Fore.GREEN           = ""	
		Fore.YELLOW          = ""
		Fore.BLUE            = ""
		Fore.MAGENTA         = ""	
		Fore.CYAN            = ""	
		Fore.WHITE           = ""
		Fore.RESET           = ""

	# These are fairly well supported, but not part of the standard.
		Fore.LIGHTBLACK_EX   = ""
		Fore.LIGHTRED_EX     = ""
		Fore.LIGHTGREEN_EX   = ""
		Fore.LIGHTYELLOW_EX  = ""
		Fore.LIGHTBLUE_EX    = ""
		Fore.LIGHTMAGENTA_EX = ""
		Fore.LIGHTCYAN_EX    = ""
		Fore.LIGHTWHITE_EX   = ""

#######################################################


	

def isEarseAction(action_value):
	"""
		check if the action is earsing rule
	""" 
	return (action_value == DISSOLVE_ACTION or action_value == DISSOLVE_ACTION_SYMBOL 
		 or action_value == ERASING_ACTION or action_value == ERASING_OUTPUT_SYMBOL)	
def isDissolveAction(action_value):
	"""
		check if actions is dissolve membrane
	""" 
	return (action_value == DISSOLVE_ACTION or action_value == DISSOLVE_ACTION_SYMBOL)	
class WrongSeconds(Exception):
	def __str__(self):
		return "Wrong amount of seconds passed (greater or equal 60)"
    
class WrongMinutes(Exception):
	def __str__(self):
		return "Wrong amount of minutes passed (greater or equal 60)"

class MembraneObject():
	"""
		MembraneObject encapsulate membrane object, name and desc 
	"""
	def __init__(self,obj, desc=None) -> None:
		self.object = obj
		self.desc = desc
	def __eq__(self, other_obj):
		# Equality Comparison between two objects
		if isinstance(other_obj,str):
			return self.object == other_obj
		if isinstance(other_obj,MembraneObject):
			return self.object == other_obj.object
		
		return False
 
	def __hash__(self):
		# hash(custom_object)
		return hash(self.object)
	def __str__(self) -> str:
		return self.object
	def __repr__(self) -> str:
		return self.object 
	# def __getstate__(self):
	# 	return self.object  

def random_membranes_selection(membrane_group :List['Membrane'],total_size):
	"""
	random select some membrane from a group with the required total size provided
	"""
	membranes_sizes = [0]*len(membrane_group)
	for i in range(len(membrane_group)):
		membranes_sizes[i] = membrane_group[i].repr_count
	group_indices = []
	
	for i in range(len(membranes_sizes)):
		group_indices.extend([i]*membranes_sizes[i])
	random_selections = random.sample(group_indices,k=total_size)
	##################################################################
	membranes_count = [0]*len(membrane_group)
	for i in range(len(membranes_sizes)):
		membranes_count[i] = random_selections.count(i)
	return membranes_count

class Rule(object):
	"""
	Rule format 
	input -> output
	rule is not assoicated with a particular membrane rather to all membrane of a particular class
	"""
	_logger  = logging.getLogger("Rule")
	def __init__(self,name, psystem) -> None:
		# Rule name
		self.name = name
		# Rule group name if this rule is part of a group of rules
		# normally nameing will follow the format 
		# r1.0 
		# r1.1
		# r1.2
		# the group name will be r1
		# and only one rule will be selected from the group based on the PPP value
		self.name_group = get_rule_name_group(name)
		self.psystem : PSystem = psystem
		## container membrane
		self.membrane = None
		
		self.input={}
		self.output={}
		# PERSONS_POPULATION_PERCENTAGE 0-1 max is 1 equal to 100%
		# default 100%
		self.PPP : float = RULE_DEFAULT_PPP
		# INPUT_POPULATION_PERCENTAGE 0-1 
		# default 100%
		self.IPP : float  = RULE_DEFAULT_IPP
		# RULE_PRIORITY
		# default 1, all 1 eqaul priority
		self.RPI = RULE_DEFAULT_RPI
		# RULE_PERCENTAGE probability 
		# default 100%
		self.RPR : float  = RULE_DEFAULT_RPR
		#self.targetType = 'here'
		# self.targetmembrane=None
		# self.action=None

		self.alt_rules = None
		self.selected_rule =  True


		## source target mapping
		self.from_mapping : Dict[str:str] = None
		## 
		self.output_mapping : Dict[str,List[Dict]] = {}
		
		self.input_membranes_map = {}
		self.moving_membranes = {}
		# self.output_membranes_map = {}
		
		
		if name :
			self._logger  = logging.getLogger(f"Rule:{self.name}")
	
	def is_selected_PPP(self):
		"""
			check if this rule is slelected to be inlcuded in the profile based on PPP value

		"""	
		
		return self.selected_rule

	@classmethod
	def init_from_yaml_v1(cls,name,from_yaml_obj,psystem : "PSystem"):
		"""
			this method setup rule from  YAML format V1
			## TODO :: add more details about the format
		"""
		cls._logger.debug(f"Initializing new Rule {name}")
		new_rule=cls(name=name,psystem=psystem)

		## get lower case keys
		lc_keys = set([x.lower() for x in from_yaml_obj.keys()])
		

		if UNRESOLVED_MAPPED_VALUE in from_yaml_obj :
			## this is rule group 
			## get the group here 
			rules_groups = from_yaml_obj[UNRESOLVED_MAPPED_VALUE]
			ppp_list = []
			total_ppp = 0
			for alt_rule in rules_groups:
				if PROPERTY_PERSONS_POPULATION_PERCENTAGE in alt_rule :
					ppp_value = alt_rule[PROPERTY_PERSONS_POPULATION_PERCENTAGE]
					if ppp_value > 1 :
						cls._logger.warning(f"Rule {name} alternative PPP={ppp_value} is > 1. Value will be adjusted to percentage to {ppp_value/100:.3f}")
						ppp_value = ppp_value/100.0
					total_ppp+=ppp_value
					ppp_list.append(ppp_value)
				else :
					cls._logger.warning(f"Rule {name} alternative does not have a PPP value. it will be assumed as zero, otherwise please specify your own value")
					ppp_list.append(0.0)
			if total_ppp < 1 :
				rules_groups.append(None)
				ppp_list.append(1-total_ppp)
			rule_def_choice_i = random.choices(range(0,len(rules_groups)), weights=ppp_list)[0]
			rule_def_choice = rules_groups[rule_def_choice_i]
			new_rule.alt_rules = []
			for i in range(0,len(rules_groups)):
				if i == rule_def_choice_i:
					new_rule.name = f"{name}.{i}"
					new_rule.name_group = name
					pass
				elif rules_groups[i] == None :
					pass
				else :
					alt_rule_name = f"{name}.{i}"
					alt_rule = Rule.init_from_yaml_v1(alt_rule_name,rules_groups[i],psystem)
					alt_rule.selected_rule = False
					alt_rule.name_group = name
					psystem._rejected_rules.append(alt_rule)
					new_rule.alt_rules.append(alt_rule)
			if rule_def_choice :
				from_yaml_obj = rule_def_choice
				new_rule.selected_rule = True
			else:
				from_yaml_obj = {PROPERTY_PERSONS_POPULATION_PERCENTAGE:1-total_ppp}
				new_rule.selected_rule = False

		def_keys = set(from_yaml_obj.keys())

		key_diff = def_keys.difference(RULE_PROPERTY_SET)
		if len(key_diff) > 0 :
			raise InValidFormat(f"Got unexpected properties keys in Rule: {name} > {key_diff}")

		#### Just for debug ##
		
		# if name == "r41" :
		# 	print(name)
	  
		## TODO :: nomalize percentage values between 1-0
		if  PROPERTY_PERSONS_POPULATION_PERCENTAGE in from_yaml_obj:
			new_rule.PPP = from_yaml_obj[PROPERTY_PERSONS_POPULATION_PERCENTAGE]
			if new_rule.PPP > 1 : 
				cls._logger.warn(f"Rule {name} PPP={new_rule.PPP} is > 1. Value will be adjusted to percentage to {new_rule.PPP/100:.3f}")
				new_rule.PPP = new_rule.PPP/100.0
		if  PROPERTY_INPUT_POPULATION_PERCENTAGE in from_yaml_obj:
			new_rule.IPP=from_yaml_obj[PROPERTY_INPUT_POPULATION_PERCENTAGE]
			if new_rule.IPP > 1 : 
				cls._logger.warn(f"Rule {name} IPP={new_rule.IPP} is > 1. Value will be adjusted to percentage to {new_rule.IPP/100:.3f}")
				new_rule.IPP = new_rule.IPP/100.0
		if  PROPERTY_RULE_PRIORITY in from_yaml_obj:
			new_rule.RPI=from_yaml_obj[PROPERTY_RULE_PRIORITY]
		if  PROPERTY_RULE_PERCENTAGE in from_yaml_obj:
			new_rule.RPR=from_yaml_obj[PROPERTY_RULE_PERCENTAGE]
			if new_rule.RPR > 1 : 
				cls._logger.warn(f"Rule {name} RPR={new_rule.RPR} is > 1. Value will be adjusted to percentage to {new_rule.RPR/100:.3f}")
				new_rule.RPR = new_rule.RPR/100.0
		
		## TODO :: check we still need the actions ?
		if  PROPERTY_ACTION in from_yaml_obj:
			new_rule.action=from_yaml_obj[PROPERTY_ACTION]
		
		if  PROPERTY_MEMBRANE in from_yaml_obj:
			## for now just store membrane name
			new_rule.membrane = from_yaml_obj[PROPERTY_MEMBRANE]

			#membranes = psystem._membranes
		else :
			## what happen to rules that do not mention a membrane name
			cls._logger.warning(f"Rule {name} does not have membrane property.")
			#new_rule.membrane = psystem._skin_membrane

		if PROPERTY_INPUT in from_yaml_obj:
			rule_input = copy.deepcopy(from_yaml_obj[PROPERTY_INPUT])
			#new_state = copy.deepcopy(m_state)
			## normalize all inputs and outputs
			#if new_rule.membrane :
			#	rule_input = {PROPERTY_MEMBRANES:[{new_rule.membrane:rule_input}]}
			## if no membrane containers then use the provided list as normal and we are going to interpret it
			rule_input = cls._get_rule_hand_side(rule_input)

			## here check and normalize
			new_rule.input = rule_input
		## TODO :: validate input and warn if empty

		if PROPERTY_OUTPUT in from_yaml_obj:
			rule_output = from_yaml_obj[PROPERTY_OUTPUT]
			if isinstance(rule_output,str) :
				## check if is has an actions
				new_rule.output = rule_output
			else :
				rule_output = copy.deepcopy(rule_output)
				#if new_rule.membrane :
				#	rule_output = {PROPERTY_MEMBRANES:[{new_rule.membrane:rule_output}]}
				rule_output = cls._get_rule_hand_side(rule_output)
				new_rule.output = rule_output
		else :
			## TODO :: validate rules
			new_rule.output = DISSOLVE_ACTION_SYMBOL
			pass

		if not new_rule.alt_rules and new_rule.PPP < 1 :
			## rule selection for a profile based on PPP value of the rule
			rule_choice = random.choices([True,False], weights=[new_rule.PPP,1-new_rule.PPP])[0]
			if rule_choice :
				new_rule.selected_rule = True
			else:
				new_rule.selected_rule = False



		if PROPERTY_FROM_MAPPING in from_yaml_obj:			
			## custom membrane mapping
			new_rule.from_mapping = from_yaml_obj[PROPERTY_FROM_MAPPING]
			


		# handle PROPERTY_PROCESS




		if not new_rule.selected_rule and not PROPERTY_INPUT in from_yaml_obj:
			return new_rule
		new_rule.__normalize()
		cls._logger.debug(f"Rule Create {name} = {new_rule}")
		return new_rule
	



	@classmethod
	def _get_rule_hand_side(cls,new_state):
		"""
			normalize membranes in rule left and right hand side
			Parse rule input and output status
			add defaults Number if not provided
			Method assocated with YAML format V1
		"""
		#import copy
		#new_state = copy.deepcopy(m_state)
		## get and unpack objects first
		if PROPERTY_OBJECTS in new_state :
			new_state[PROPERTY_OBJECTS] = unpackListAsDict(new_state[PROPERTY_OBJECTS])
			for o_key in new_state[PROPERTY_OBJECTS]:
				obj = new_state[PROPERTY_OBJECTS][o_key]
				if not isinstance(obj,dict):
					unresolved_value = unresolved_value_to_dict(obj)
					new_state[PROPERTY_OBJECTS][o_key] = unresolved_value
				obj = new_state[PROPERTY_OBJECTS][o_key]
				if PROPERTY_ACTION in obj :
					## normalize actions value
					action_value = obj[PROPERTY_ACTION]
					# for objects dissolve is equal to erase
					if (action_value ==  DISSOLVE_ACTION_SYMBOL 
		 						or action_value == DISSOLVE_ACTION
								 or action_value == ERASING_OUTPUT_SYMBOL ):
						action_value = ERASING_ACTION
					obj[PROPERTY_ACTION] = action_value
				# yaml.dump(x, open("data.yml","w"), default_flow_style=False)
		if PROPERTY_MEMBRANES in new_state :
			#rules_in_membranes = new_state[PROPERTT_MEMBRANES].copy()
			unpackList(new_state[PROPERTY_MEMBRANES],PROPERTY_MEMBRANE)
			for membrane in new_state[PROPERTY_MEMBRANES] :
				if UNRESOLVED_MAPPED_VALUE in membrane :
					unresolved_value = membrane[UNRESOLVED_MAPPED_VALUE]
					unresolved_value = unresolved_value_to_dict(unresolved_value)
					if unresolved_value :
						membrane.update(unresolved_value)
						del membrane[UNRESOLVED_MAPPED_VALUE]
				if not PROPERTY_N in membrane:
					## default to 1 
					membrane[PROPERTY_N] = 1
				cls._get_rule_hand_side(membrane)

			#unpackList(rules_in_membranes,"membrane")
			#new_state[PROPERTY_OBJECTS] = rules_in_membranes
		return new_state	

	@classmethod
	def getHSStatusStr(cls,hs_part):
		"""
			get Rule both Hand sides as a string format
			hs_part : input or output side
			for debuging and logging
			return str representation of the provided part 
		"""
		input_om_str = ""
		#input_ms_str = ""

		if PROPERTY_OBJECTS in hs_part:
			for o_key in hs_part[PROPERTY_OBJECTS] :
				obj = hs_part[PROPERTY_OBJECTS][o_key] 
				n = 1
				if PROPERTY_N in obj:
					n = obj[PROPERTY_N]
				if PROPERTY_ACTION in obj and (
					isEarseAction(obj[PROPERTY_ACTION])
				):
					## do not write it
					#input_om_str += f"{Fore.LIGHTYELLOW_EX}{ERASING_OUTPUT_SYMBOL}({Fore.GREEN}{n}{Fore.YELLOW}{o_key}{Fore.LIGHTYELLOW_EX}){Fore.RESET}, "
					pass
				else :
					input_om_str += f"{Fore.GREEN}{n}{Fore.RESET}{Fore.BLUE}{o_key}{Fore.RESET}, "

		# input_om_str = input_om_str.strip() 
		# if len(input_os_str) > 0 :
		# 	if input_os_str[-1] == ",":
		# 		input_os_str = input_os_str[:-1]
		# input_os_str = input_os_str.strip() 

		if PROPERTY_MEMBRANES in hs_part:
			for membrane in hs_part[PROPERTY_MEMBRANES]:
				membrane_num_str = ""
				membrane_name = membrane[PROPERTY_MEMBRANE]
				if PROPERTY_N in membrane and membrane[PROPERTY_N]>1 :
					membrane_num_str = f"{Fore.GREEN}{membrane[PROPERTY_N]}{Fore.RESET}"
				if (PROPERTY_ACTION in membrane  and
						(membrane[PROPERTY_ACTION] == DISSOLVE_ACTION or 
	   					membrane[PROPERTY_ACTION] == DISSOLVE_ACTION_SYMBOL  ) ):
					input_om_str += f"{membrane_num_str}{Fore.LIGHTYELLOW_EX}[{DISSOLVE_ACTION_SYMBOL}]{Fore.RESET}{Fore.YELLOW}{membrane_name}{Fore.RESET}, "
				else :	
					membrane_hs_str = cls.getHSStatusStr(membrane)
					input_om_str += f"{membrane_num_str}[{membrane_hs_str}]{Fore.RED}{membrane_name}{Fore.RESET}, "
		input_om_str = input_om_str.strip()


		if len(input_om_str) > 0 :
			if input_om_str[-1] == ",":
				input_om_str = input_om_str[:-1]
		input_om_str = input_om_str.strip() 
		# if input_os_str and input_ms_str :
		# 	return f"{input_os_str} {input_ms_str} "
		# if not input_os_str and  input_ms_str :
		# 	return f" {input_ms_str} "
		# if input_os_str and not input_ms_str :
		# 	return f"{input_os_str}"
		if input_om_str == "":
			return ""
		return f" {input_om_str} "

	def __str__(self,input_only=False,output_only=False,no_atts=False) -> str:
		"""
		get a string representation to the rule
		"""
		membrane = ""
		if self.membrane :
			membrane = self.membrane
		input_str = ""
		output_in_str = ""
		output_out_str = ""
		## get all inputs
		input_str = Rule.getHSStatusStr(self.input)
		## get outputs 
		output_str = Rule.getHSStatusStr(self.output)
		
		## add an proprity if not default
		rule_properties_str = ""

		if not no_atts :
			if self.PPP != RULE_DEFAULT_PPP :
				rule_properties_str += f"{Fore.CYAN}PPP{Fore.RESET}={Fore.GREEN}{self.PPP:.3f}{Fore.RESET},"
			if self.IPP != RULE_DEFAULT_IPP :
				rule_properties_str += f"{Fore.CYAN}IPP{Fore.RESET}={Fore.GREEN}{self.IPP:.3f}{Fore.RESET},"
			if self.RPI != RULE_DEFAULT_RPI :
				rule_properties_str += f"{Fore.CYAN}RPI{Fore.RESET}={Fore.GREEN}{self.RPI}{Fore.RESET},"
			if self.RPR != RULE_DEFAULT_RPR :
				rule_properties_str += f"{Fore.CYAN}RPR{Fore.RESET}={Fore.GREEN}{self.RPR:.3f}{Fore.RESET},"

			if str.lower(self.name) != RULE_DEFAULT_NAME :
				rule_properties_str += f"{Fore.CYAN}Name{Fore.RESET}={Fore.GREEN}{self.name}{Fore.RESET},"
			rule_properties_str = rule_properties_str.strip() 
			if len(rule_properties_str) > 0 :
				if rule_properties_str[-1] == ",":
					rule_properties_str = rule_properties_str[:-1]
			rule_properties_str = rule_properties_str.strip() 
			if rule_properties_str :
				rule_properties_str = f"\t({rule_properties_str})"


		# TODO :: what is the best way to write altrnative rules 
		alt_rules_str = ""
		# if self.alt_rules :
		# 	for alt_rule in self.alt_rules :
		# 		alt_rules_str = f"{alt_rules_str}\n{alt_rule.__str__()}"

		#if membrane :
		#	return f"[{input_str}]{Fore.RED}{membrane}{Fore.RESET} -> {output_out_str}[{output_str}]{Fore.RED}{membrane}{Fore.RESET}{rule_properties_str}{alt_rules_str}"
		
		#if self.input_membrane :
		#	input_str = f"[{input_str}]{Fore.RED}{self.input_membrane}{Fore.RESET}"
		#if self.output_membrane :
		#	output_str = f"[{output_str}]{Fore.RED}{self.output_membrane}{Fore.RESET}"
		if input_only:
			return f"{input_str}"
		return f"{input_str} -> {output_str}{rule_properties_str}{alt_rules_str}"


	@classmethod
	def _get_all_membranes_name(cls,io_part,level=1, parent_mem= None, parent_entry=None, n_multiplier=1):
		
		final_list = []
		for _mem in io_part :
			membrane_info = {}
			_mem_name = _mem[PROPERTY_MEMBRANE]
			_mem_full_name = _mem[PROPERTY_MEMBRANE]
			if parent_mem:
				_mem_full_name = f"{parent_mem}.{_mem_name}"
				membrane_info[PROPERTY_PARENT] = parent_mem
				membrane_info['parent_entry'] = parent_entry
			membrane_info[PROPERTY_NAME] = _mem_name
			membrane_info['input_node'] = _mem
			#membrane_info['input_node_parent'] = _mem
			membrane_info[PROPERTY_FCMN] = _mem_full_name
			membrane_info[PROPERTY_LEVEL] = level
			membrane_info[PROPERTY_N] = 1
			if PROPERTY_N in _mem : ## no need to check it that is the case
				membrane_info[PROPERTY_N] = _mem[PROPERTY_N]
			membrane_info['total_number'] = n_multiplier*membrane_info[PROPERTY_N]
			final_list.append(membrane_info)
			
			if PROPERTY_MEMBRANES in _mem:
				sub_final_list = Rule._get_all_membranes_name(_mem[PROPERTY_MEMBRANES],level+1, _mem_full_name,membrane_info,membrane_info['total_number'])
				final_list.extend(sub_final_list)

		return final_list


	def __normalize(self):
		"""
		normalize input and output
		perfrom validation of the rule and make sure we can apply it
		"""
		container_membrane = self.membrane
		input_membranes_list = []
		output_membranes_list = []
		if not isinstance(self.input,dict):
			raise ValueError(f"Rule:{self.name} input format are not supported.")
		if not isinstance(self.output,dict):
			raise ValueError(f"Rule:{self.name} input format are not supported.")
		if PROPERTY_MEMBRANES in self.input:
			input_membranes_list = Rule._get_all_membranes_name(self.input[PROPERTY_MEMBRANES])
		## validate inputs first
		## check container_membrane 
		in_level_1_count = sum([1 for _m in input_membranes_list if _m['level'] == 1 ])
		if in_level_1_count > 1 :
			raise ValueError(f"Rule{self.name} has multiple input main membranes, which is not supported in this version")
		main_membrane = None
		input_main_membrane=""
		if in_level_1_count == 1:
			main_membrane =  next((_m for _m in input_membranes_list if _m['level'] == 1 ), None)
			input_main_membrane = main_membrane['name']
			# if not main_membrane:
			# 	self._logger.warning(f"Rule:{self.name} container Membrane: {container_membrane} is explicitly mentioned in the input list")

			# 	self.input_membrane = container_membrane
			# 	## normalize the input as membrane
			# 	self.input[PROPERTY_MEMBRANE] = container_membrane
			# 	self.input = {PROPERTY_MEMBRANES:[self.input]}
			# 	input_membranes_list = Rule.__get_all_membranes_name(self.input[PROPERTY_MEMBRANES])
			# else:
			# 	self.input_membrane = None
		## if there is a container membrane input and output are inside the containers
		## CHECK if the container membrane is in the list of input or output

		if container_membrane and container_membrane != input_main_membrane :
			## 
			raise ValueError(f"Rule{self.name} container membrane is not the same as the input main membrane. Please fix.")
		if not container_membrane and not input_main_membrane :
			raise ValueError(f"Rule{self.name} can not detect container membrane. Please fix.")

		if not container_membrane:
			container_membrane = input_main_membrane
		
		self._logger.debug(f"Rule:{self.name} Container Membrane: {container_membrane}")
		
		if PROPERTY_MEMBRANES in self.output:
			output_membranes_list = Rule._get_all_membranes_name(self.output[PROPERTY_MEMBRANES])
		
		main_output_membrane =  next((_m for _m in output_membranes_list if _m['name'] == container_membrane), None)
		if not main_output_membrane :
			self._logger.warning(f"Rule:{self.name} container Membrane: {container_membrane} is not mentioned in the output list. Will assume it will be dissolved.")


		#self._logger.debug(f"Rule:{self.name} has no container membrane, Input and Output must be explict.")
		#out_level_1_count = sum([1 for _m in output_membranes_list if _m['level'] == 1 ])
		#in_level_1_count = sum([1 for _m in input_membranes_list if _m['level'] == 1 ])

		## TODO :: check total 	
		input_membranes_map = {}
		for input_membrane in input_membranes_list :
			if input_membrane[PROPERTY_NAME] in input_membranes_map:
				error_msg = f"Multiple occurences of Membrane{input_membrane[PROPERTY_NAME]} Multiple reference of one membrane in different location in the is not supported."
				self._logger.error(error_msg)
				raise InValidFormat(error_msg)
			input_membranes_map[input_membrane[PROPERTY_NAME]] = input_membrane 
			input_membrane["output_count"] = 0
			input_membrane["total_output_count"] = 0
			input_membrane["self_count"] = 0
			input_membrane["total_self_count"] = 0
			input_membrane["moving_count"]=0
			input_membrane["total_moving_count"]=0
			input_membrane[K_OUTPUT_MEMBRANES] = []
			input_membrane["input_node"]["map_entry"] = input_membrane
		self.input_membranes_map = input_membranes_map
		self._expand_output(self.output)

		## check dissolving membranes
		for input_membrane_name,input_membrane in self.input_membranes_map.items() :
			input_count = 	input_membrane[PROPERTY_N]
			output_count = input_membrane["output_count"]
			self_count = input_membrane["self_count"] 
			total_input_count = input_membrane[K_TOTAL_NUMBER]
			total_output_count = input_membrane[K_TOTAL_OUTPUT_COUNT]
			input_count = total_input_count
			output_count = total_output_count
			if total_input_count != total_output_count :
				self._logger.warning(f"In Rule:{self.name} membrane {input_membrane_name} has unbalanced input and output. I will try to fix it, please revise")
			#	raise ValueError(f"In Rule:{self.name} membrane {input_membrane_name} has unbalanced input and output, please fix")
			if input_count < output_count : ## require cloneing
				## TODO  to be tested
				extra_clones = output_count - input_count
				if input_membrane[PROPERTY_LEVEL] > 1 :
					extra_clones = extra_clones//input_membrane['parent_entry'][K_TOTAL_OUTPUT_COUNT]
				self._logger.warning(f"In Rule:{self.name} membrane {input_membrane_name} will produce {extra_clones} extra clone")
				input_membrane['input_node']['extra_clones'] = extra_clones
				pass
			if output_count < input_count :
				## some will dissolve ?? warn here
				missing_count = input_count - output_count
				if input_membrane[PROPERTY_LEVEL] > 1 :
					if missing_count % input_membrane["parent_entry"][K_TOTAL_OUTPUT_COUNT] != 0 :
						raise ValueError(f"In Rule:{self.name} membrane {input_membrane_name} has unbalanced input and output. please fix")
					missing_count = missing_count/input_membrane["parent_entry"][K_TOTAL_OUTPUT_COUNT]
				# there is not corrsponoing output just add it in the same place
				if PROPERTY_PARENT in input_membrane:
					parent_membrane_output = input_membrane["parent_entry"][K_OUTPUT_MEMBRANES][-1] ## TODO :: POSSIBLE SOLUTION TO THE PROBLEM
				else:
					raise ValueError(f"Rule {self.name} hase unsupported logic for {input_membrane_name}")
				## or
				#	if len(input_membrane[K_OUTPUT_MEMBRANES]) > 0:
				#		parent_membrane_output = input_membrane[K_OUTPUT_MEMBRANES][-1]['parent']	
				if not PROPERTY_MEMBRANES in parent_membrane_output :
					parent_membrane_output[PROPERTY_MEMBRANES] = []

				
				new_membrane_def = {
						PROPERTY_MEMBRANE:input_membrane_name,
						PROPERTY_N : missing_count,
						PROPERTY_ACTION:DISSOLVE_ACTION,
						K_SOURCE_MAPPING : input_membrane_name,
						PROPERTY_FCMN : input_membrane[PROPERTY_FCMN],
						PROPERTY_PARENT : parent_membrane_output,
						K_TOTAL_NUMBER: missing_count * parent_membrane_output[K_TOTAL_NUMBER]
				}
				parent_membrane_output[PROPERTY_MEMBRANES].append(
					new_membrane_def
				)
				input_membrane[K_OUTPUT_MEMBRANES].append(new_membrane_def)
				input_membrane["output_count"] += missing_count
				input_membrane["self_count"]  += missing_count
				input_membrane["total_output_count"] += missing_count * parent_membrane_output[K_TOTAL_NUMBER]
				input_membrane["total_self_count"] += missing_count * parent_membrane_output[K_TOTAL_NUMBER]
				pass
			if self_count < output_count:
				## some will be renamed ??
				pass
			## does self require moving 
			## for each _membrane in output_membranes check
			input_membrane[K_OUTPUT_MEMBRANES]
		return None
		## check if container_membrane is in input list [explict member probaly something coming from outside]
		## check if container_membrane is in ouput list [explict member probaly something going to the outside]
		# output_membranes_map = {}
		# for output_membrane in output_membranes_list :
		# 	output_membrane_name = output_membrane[PROPERTY_NAME]
		# 	output_membranes_map[output_membrane[PROPERTY_FCMN]] = output_membrane
		# 	## it come from a same name
		# 	source_mapping = output_membrane_name
		# 	if self.from_mapping and output_membrane_name in self.from_mapping:
		# 		source_mapping = self.from_mapping[output_membrane_name]
		# 	if not source_mapping in self.output_mapping:
		# 		self.output_mapping[source_mapping] = []
			
		# 	## determine the final action action
		# 	if source_mapping in input_membranes_map:
		# 		input_membranes_map[source_mapping]["output_count"] += output_membrane[PROPERTY_N]
		# 		if source_mapping == output_membrane[PROPERTY_NAME]:
		# 			input_membranes_map[source_mapping]["self_count"] += output_membrane[PROPERTY_N]
		# 			## parent check here
		# 		else:
		# 			output_membrane[PROPERTY_ACTION] = CLONE_ACTION
		# 		# output_membrane["source"] = input_membranes_map[source_mapping]
		# 	else:
		# 		## must be new or we can not determine origin
		# 		output_membrane[PROPERTY_ACTION] = CREATE_ACTION
		# 	self.output_mapping[source_mapping].append(output_membrane)
		
		# self.output_membranes_map = output_membranes_map
	
	def _expand_output(self, _output, parent_fcmn = None , level=1):
		
		if not PROPERTY_MEMBRANES in _output:
			return
		n_multiplier = 1
		if "total_number" in _output:
			n_multiplier = _output["total_number"]

		for _membrane in _output[PROPERTY_MEMBRANES]:
			output_membrane_name = _membrane[PROPERTY_MEMBRANE]

			
			membrane_fcmn = output_membrane_name
			if parent_fcmn :
				membrane_fcmn = f"{parent_fcmn}.{output_membrane_name}"

			_membrane[K_SOURCE_MAPPING] = None
			_membrane[PROPERTY_LEVEL] = level		
			_membrane[PROPERTY_FCMN] = membrane_fcmn
			_membrane[PROPERTY_PARENT] = _output

			n_count = 1
			if PROPERTY_N in _membrane:
				n_count = _membrane[PROPERTY_N]
			_membrane["total_number"] = n_count*n_multiplier
			source_mapping = output_membrane_name
			if self.from_mapping and output_membrane_name in self.from_mapping:
				source_mapping = self.from_mapping[output_membrane_name]
			if source_mapping in self.input_membranes_map:
				self.input_membranes_map[source_mapping]["output_count"] += n_count #*n_multiplier
				self.input_membranes_map[source_mapping]["total_output_count"] += n_count*n_multiplier
				if source_mapping == output_membrane_name:
					self.input_membranes_map[source_mapping]["self_count"] += n_count
					self.input_membranes_map[source_mapping]["total_self_count"] += n_count*n_multiplier

					## parent check here
				else:
					## move 
					_membrane[CLONE_ACTION] = True
				self.input_membranes_map[source_mapping][K_OUTPUT_MEMBRANES].append(_membrane)
				input_level = self.input_membranes_map[source_mapping][PROPERTY_LEVEL]
				if abs(input_level - level) > 1 :
					raise ValueError(f"Output Membrane : {output_membrane_name} in Rule {self.name} can not move 2 levels in one step. Please fix.")
				
				if membrane_fcmn != self.input_membranes_map[source_mapping][PROPERTY_FCMN] :
					out_parnet = None
					input_parent = None
					if PROPERTY_PARENT in _membrane:
						out_parnet = _membrane[PROPERTY_PARENT][PROPERTY_FCMN]
					if PROPERTY_PARENT in self.input_membranes_map[source_mapping]:
						input_parent = self.input_membranes_map[source_mapping][PROPERTY_PARENT]
					## moving from one membane to  another
					if out_parnet != input_parent :
						_membrane[MOVE_ACTION] = True
						self.input_membranes_map[source_mapping][MOVE_ACTION]=True
						self.input_membranes_map[source_mapping]["moving_count"] += n_count #*n_multiplier
						self.input_membranes_map[source_mapping]["total_moving_count"] += n_count * n_multiplier
						self.moving_membranes[membrane_fcmn] = _membrane

			else:
				_membrane[CREATE_ACTION] = True
			_membrane[K_SOURCE_MAPPING] = source_mapping

			
			self._expand_output(_membrane,membrane_fcmn,level+1)
		


	def __repr__(self) -> str:
		#return '<%s:%s(%s)>' % (self.name, self.membrane)
		return f"{self.name}:{self.membrane}"

	def __eq__(self, other):
		## check if equal 
		return (
        self.__class__ == other.__class__ and
             self.membrane == other.membrane and 
             self.name == other.name
    	) 

	def __ne__(self, other):	
		return not self.__eq__(other)
	
	@property
	def membrane_level(self):
		'''
		get rule membrane level
		useful for sorting rules 
		TODO :: current vertion only support one input 
		'''
		membranes_list = self.psystem.get_membrane(self.membrane)
		if membranes_list :
			if len(membranes_list) == 0:
				return 0
			min_level = math.inf
			for membrane in membranes_list:
				min_level = min(min_level,membrane.level)
			return min_level
		return 0


	@property
	def input_membranes(self):
		"""
			return all participant membranes in the input
			TODO :: current vertion only support one input 
		"""
		_input_membranes =  [self.input_membranes_map[_mk] for _mk in self.input_membranes_map  if self.input_membranes_map[_mk]['level'] == 1 ]
		return _input_membranes

	
	
###########################

	
	def get_input(self,membrane_name):
		"""
		return an input repr of the membrane_name 
		"""	
		for _mem in self.input[PROPERTY_MEMBRANES]:
			if _mem[PROPERTY_MEMBRANE] == membrane_name:
				return _mem
		raise ValueError(f"Membrane:{membrane_name} is not part of rule:{self.name}")
	def get_output(self,membrane_name):
		"""
		return an output repr of the membrane_name 
		"""	
		for _mem in self.output[PROPERTY_MEMBRANES]:
			if _mem[PROPERTY_MEMBRANE] == membrane_name:
				return _mem
		raise ValueError(f"Membrane:{membrane_name} is not part of rule:{self.name}")
	
	
	
	
	
 
	


		
	

class Membrane():
	_logger  = logging.getLogger("Membrane")
	@classmethod
	def init_from_def(cls,membrane_def,p_system, repr_count = 1):
		"""
			initialize new membrane from an input definition
			Definition Format :
			## TODO :: add format here
		"""
		membrane_name = membrane_def[PROPERTY_MEMBRANE]
		# cls._logger.debug(f"Creating Membrane {membrane_name}")
		new_membrane = cls(membrane_name,p_system=p_system, repr_count=repr_count)

		## init objects
		if PROPERTY_OBJECTS in membrane_def:
				objects = membrane_def[PROPERTY_OBJECTS]
				for obj_key in objects :
					obj_count = 1
					if PROPERTY_N in objects[obj_key]:
						obj_count = objects[obj_key][PROPERTY_N]
					obj_class = p_system.getObject(obj_key)
					new_membrane.add_objects(obj_class,obj_count)
		## init membranes
		if PROPERTY_MEMBRANES in membrane_def:
			membranes_children= membrane_def[PROPERTY_MEMBRANES]
			for child_membrane in membranes_children:
				mem_count = 1
				child_membrane_name = child_membrane[PROPERTY_MEMBRANE]
				child_membrane_definition = p_system.get_membrane_definition(child_membrane_name, True)
				## should this fail or just create an empty one
				if not child_membrane_definition :
					child_membrane_definition = {} 
				## for nested membranes structure 
				## update child_membrane_definition with child_membrane
				## TODO :: require testing
				child_membrane_definition.update(child_membrane)
				if PROPERTY_N in child_membrane:
						mem_count = child_membrane[PROPERTY_N]
				#mem_count=1
				## creating an instance for each one : going this direction  take a lot of mem and time
				## alternatve solution is to create a represtative membrane for all count
				## and divide the count later once changed
				if compress_membranes :
					new_child_mem = Membrane.init_from_def(child_membrane_definition,p_system, mem_count)
					new_membrane.add_membrane(new_child_mem)
				else:
					for i in range(0,mem_count):
						new_child_mem = Membrane.init_from_def(child_membrane_definition,p_system)
						new_membrane.add_membrane(new_child_mem)
				#new_membrane.childrens.append(child)
		#cls._logger.debug(f"\t\tMembrane: {membrane_name} created.")
		
		return new_membrane
	
##################################################################################
############             public                       ############################
############             interface                    ############################
##################################################################################
	def add_objects(self,object_key,count=1, reset=False):
		"""
			take an object key and increment it be the  provided count or add it if it does not exist 

			return new Object Count
		"""
		if isinstance(object_key,str):
			object_key = self.p_system.getObject(object_key)
		if not object_key in self.objects:
			self.objects[object_key] = 0
		old_count = self.objects[object_key]
		if reset:
			new_count = count
		else:
			new_count = old_count + count
		self.objects[object_key] = new_count
		## altr strucutre subject to remove or keep depending on the need
		if not PROPERTY_OBJECTS in self.membrane_status:
			self.membrane_status[PROPERTY_OBJECTS]={}
		if isinstance(object_key,MembraneObject) :
			self.membrane_status[PROPERTY_OBJECTS][object_key.object] = new_count
		elif isinstance(object_key,str) :
			self.membrane_status[PROPERTY_OBJECTS][object_key] = new_count
		return new_count
	

	def remove_objects(self,object_key,count=1):
		"""
			take an object key and decrease  it be count provided
			or remove it if the new count is zero
			return new count
			raise an error if object does not exist or no enough Objects in the membrane
		"""
		if not object_key in self.objects:
			raise ValueError(f"No such Objects:{object_key} in Membrane:{self.name} to remove")
		old_count = self.objects[object_key]
		if old_count < count :
			raise ValueError(f"No enough Objects to remove Membrane:{self.name} has {old_count}:{object_key}, however {count}:{object_key} is needed.")

		new_count = old_count - count
		self.objects[object_key] = new_count
		if new_count == 0 :
			del self.objects[object_key]
		## altr strucutre subject to remove or keep depending on the need
		_object_key = object_key
		if isinstance(object_key,MembraneObject):
			_object_key = object_key.object
		if new_count == 0 :
			del self.membrane_status[PROPERTY_OBJECTS][_object_key]
		else :
			self.membrane_status[PROPERTY_OBJECTS][_object_key] = new_count
		
		if len(self.membrane_status[PROPERTY_OBJECTS]) == 0 :
			del self.membrane_status[PROPERTY_OBJECTS]

		return new_count

	def add_membrane(self,child_membrane : 'Membrane', merge_membranes = False):
		"""
			add new child_membrane to this membrane childrens
			merge_membranes : not implmented right now
			return internal id of the child membrane
		"""
		if merge_membranes :
			self._logger.warn("merge_membranes options is not implemented in add_membrane, option will be ignore")
			pass

		membrane_name = child_membrane.name
		## do not assign new id to it
		mem_id = child_membrane.id
		if not membrane_name in self.childrens_group:
			## init new group
			self.childrens_group[membrane_name] = []
			self.childrens_group_ids[membrane_name] = set()
		## ensure a unique id
		if not mem_id :  
			while True:
				mem_id = membrane_name + "." + get_random_string(10)
				if not mem_id in self.childrens_group_ids[membrane_name]:
					break
			child_membrane.id = mem_id
		self.childrens_group[membrane_name].append(child_membrane)
		self.childrens_group_ids[membrane_name].add(mem_id)
		child_membrane.parent = self

		## maintain altr strucutre
		if not PROPERTY_MEMBRANES in self.membrane_status :
			## create it 
			self.membrane_status[PROPERTY_MEMBRANES] = {}
		self.membrane_status[PROPERTY_MEMBRANES][child_membrane.id] = child_membrane.membrane_status
		self.p_system.add_membrane(child_membrane)
		return mem_id		 

	def remove_membrane(self,child_membrane : 'Membrane'):
		"""
			remove the child_membrane from the child list of this membrane
		"""
		membrane_name = child_membrane.name
		self.childrens_group[membrane_name].remove(child_membrane)
		self.childrens_group_ids[membrane_name].remove(child_membrane.id)
		if len(self.childrens_group[membrane_name]) == 0:
			del self.childrens_group[membrane_name]
		if len(self.childrens_group_ids[membrane_name]) == 0:
			del self.childrens_group_ids[membrane_name]

		del self.membrane_status[PROPERTY_MEMBRANES][child_membrane.id]
		if len(self.membrane_status[PROPERTY_MEMBRANES]) == 0:
			del self.membrane_status[PROPERTY_MEMBRANES]
		child_membrane.id = None
		child_membrane.parent = None
		self.p_system.remove_membrane(child_membrane)

	def move_to (self,new_parent : 'Membrane'):
		"""
		move a membrane to a new container membrane
		move must be validated before ??
		supported move  [[]y]x -> []y[]x    , []y[]x -> [[]y]x  , [[]z]y[]x -> []y[[]z]x  
		"""
		## it is better to keep same id
		if not new_parent :
			## free state for some time
			if self.parent :
				__keep_id = self.id
				new_count =  self.repr_count * self.parent.total_repr_count
				self.parent.remove_membrane(self)
				self.id = __keep_id
				self.repr_count = new_count
			return
		if self.parent :
			__keep_id = self.id
			old_parent_count =  self.parent.repr_count
			old_parent_level = self.parent.level

			## once moved out
			self.parent.remove_membrane(self)
			#self.repr_count *= old_parent_count
			if __keep_id :
				self.id = __keep_id
			## other logic here
			self.is_locked = False
			## for this new membrane merge with existing one if we have
			new_parent.add_membrane(self, merge_membranes=True)
			if new_parent.level == old_parent_level :
				# moving out multi by old parent count and divide by new parent count

				self.repr_count = (self.repr_count * old_parent_count)/ new_parent.repr_count
			if  new_parent.level > old_parent_level:
				## moving down on level divide by new parent count
				self.repr_count = self.repr_count / new_parent.repr_count
			if  new_parent.level < old_parent_level:
				## moving up one level
				self.repr_count = self.repr_count * old_parent_count
		else:
			## TODO :: what the count repr here
			self.is_locked = False
			## for this new membrane merge with existing one if we have
			self.repr_count = self.repr_count//new_parent.total_repr_count
			new_parent.add_membrane(self, merge_membranes=True)


	def rename (self,new_name):
		parent = self.parent
		if not self._rename_map:
			self._rename_map= {}
		## map old names 
	
		
		if parent:
			parent.remove_membrane(self)
		else:
			self.p_system.remove_membrane(self)
		
		self._rename_map[self.name ] = new_name
		self.name = new_name

		if parent:
			parent.add_membrane(self)
		else :
			self.p_system.add_membrane(self)
		pass
	
	

	
	
	
	
	#######################################################################################

	




	
   
	   
	
	
	



	def __init__(self,membrane_name,p_system : 'PSystem', repr_count=1) -> None:
		# id is init once it is added to a  parent 

		self.p_system = p_system
		
		# name and type should be in membrane_def
		## name represent a general type of membrane which is referenced in rules
		self.name = membrane_name
		#self.membrane_type = membrane_type
		#self.membrane_def = membrane_def
		
		
		## object in simle for is a counter map of differnt objects in the membrane
		self.objects : Dict[MembraneObject,int] = {}
		self.parent : Membrane = None
		## id is a unique reference for this named membrane accoss the system
		self.id = None
		## a list of all childrens
		#self.childrens : List[Membrane] = []
		self.childrens_group : Dict[str, List[Membrane]] = {} # {type1:[],type2:[]}
		
		## one way to represent count is holding it in self.childrens_count map
		## or simplly hold a representative count in each membrance on behave all similar membranes
		self._repr_count = repr_count
		## hold childs membrane ids
		## do we need ids ??
		self.childrens_group_ids : Dict[str,Set[str]] = {}
		
		self._rules = []
		self.staged_output = SortedList(key=lambda x: x["iteration"])
		## for now use dict :: TODO :: find an altrative for better runtime
		## iteration -> {rule_id : {mebrane_key : [membranes list]}}
		self.staged_membranes : Dict[int,Dict[str,List[Membrane]]]= {}
		self._map_to_staged_list = {}

		self._rename_map = None
		## staged_output 
		## {"iteration" : i, "rule"  : rule, "rule_output": , "n_output" : prop   }
		# self.active_state = True
		## active data structure to the skin 
		## can be property instead to dynamic
		self.membrane_status = {
			PROPERTY_MEMBRANE : self.name,
			#PROPERTY_OBJECTS : {},
			#PROPERTY_MEMBRANES : {},
			PROPERTY_N : self._repr_count
		}
		self._is_locked = False
		self.status_manager = None
		pass

	@property
	def is_locked(self):
		return self._is_locked
	
	@is_locked.setter
	def is_locked(self,value):

		self._is_locked = value
	
	
	
	


	def has_objects(self, input_objects : Dict[str,Dict] ):
		"""
			can b represeted by M > objects
			check if membrane has input_objects spec at least 
		"""

		if input_objects :
			obj_diff = {}
			for obj_key in input_objects:
				obj_def = input_objects[obj_key]
				required_count = 1
				if PROPERTY_N in obj_def :
					required_count = obj_def[PROPERTY_N]
				available_count = 0
				if obj_key in self.objects:
					available_count = self.objects[obj_key]
				if required_count > available_count:
					return False
				## obj_diff[obj_key] = required_count//available_count
				
		return True 
	
	

	
	
	

	
	##Done def flush_output

	

	


########################################################################################
	def get_str_status(self,nested=True, max_level=None):
		"""
			get a string representation of the Membrane status
			with colors if console color are enable, 
		"""
		input_os_str = ""
		
		object_key_sorted = list(self.objects.keys())
		object_key_sorted.sort(key=lambda x :x.object)
		for object in object_key_sorted :
			count = self.objects[object]
			count_str = count
			if math.isinf(count):
				count_str = INF_SYMBOL
			input_os_str += f"{Fore.GREEN}{count_str}{Fore.RESET}{Fore.BLUE}{object}{Fore.RESET}, "
		if nested:
			for list_name,child_list in self.childrens_group.items():
				for child_membrane in child_list :
					input_os_str += f"{child_membrane.get_str_status()}, "		
		else:
			for list_name,child_list in self.childrens_group.items():
				for child_membrane in child_list :
					leading_count = ""
					if child_membrane.repr_count > 1 :
						leading_count =f"{Fore.GREEN}{child_membrane.repr_count}{Fore.RESET}"
					input_os_str += f"{leading_count}[]{Fore.RED}{child_membrane.name}{Fore.RESET}, "

		input_os_str = input_os_str.strip() 
		
		if len(input_os_str) > 0 :
			if input_os_str[-1] == ",":
				input_os_str = input_os_str[:-1]
		input_os_str = input_os_str.strip() 

		membrane_name = self.name
		if self.parent == None:
			membrane_name=""
		rest_str=""
		

		if not nested and len(self.childrens_group)>0 and ( max_level == None or (max_level != None and max_level > 0)  ):
			tabs = "\t"*(self.level+1)
			rest_str+= f"\n{tabs}## Membrane:{self.name} children\n"
			for list_name,child_list in self.childrens_group.items():
				for child_membrane in child_list :
					new_max_level = None
					if max_level : 
						new_max_level = max_level - 1
					rest_str +=  f"{tabs}{child_membrane.get_str_status(nested=nested,max_level=new_max_level)}\n"	

		leading_count = ""
		if self.repr_count > 1 and nested:
			leading_count =f"{Fore.GREEN}{self.repr_count}{Fore.RESET}"
		return f"{leading_count}[{input_os_str}]{Fore.RED}{membrane_name}{Fore.RESET}{rest_str}"

	def write_str_status(self,fs,level=0):
		"""
			get a string representation of the Membrane status
			with colors if console color are enable, 
		"""
		tabs = "\t"*(level)
		pass_level= level
		if self.parent == None:
			pass_level=level
		else:
			pass_level+=1
			fs.write(f"{tabs}[")

		tabs = "\t"*(pass_level)
		
		
		input_os_str = ""
		#### write objectes
		object_key_sorted = list(self.objects.keys())
		object_key_sorted.sort(key=lambda x :x.object)
		for object in object_key_sorted :
			count = self.objects[object]
			count_str = count
			if math.isinf(count):
				count_str = INF_SYMBOL
			input_os_str += f"{count_str}{object}, "
		input_os_str = input_os_str.strip() 
		has_objects = False
		if len(input_os_str) > 0 :
			if input_os_str[-1] == ",":
				input_os_str = input_os_str[:-1]
		input_os_str = input_os_str.strip() 
		if len(self.childrens_group_ids) > 0 and len(input_os_str) > 0:
			input_os_str += ","
		if len(input_os_str) > 0:
			has_objects = True
			fs.write(f"\n{tabs}{input_os_str}\n")
		
		if not has_objects and len(self.childrens_group_ids) > 0:
			fs.write("\n")

		childrens_group_keys =	list(self.childrens_group.keys())
		for i in range(len(childrens_group_keys)):
				list_name = childrens_group_keys[i]
				child_list = self.childrens_group[list_name]
				for j in range(len(child_list)) :
					child_membrane = child_list[j]
					child_membrane.write_str_status(fs,pass_level)
					if j < len(child_list)-1 :
						fs.write(",\n")
				if i < len(childrens_group_keys)-1 :
					fs.write(",")
				fs.write("\n")

		tabs = "\t"*(level)
		if not has_objects and len(self.childrens_group_ids) == 0:
			tabs=""
		if self.parent == None:
			pass_level=level
		else:
			pass_level+=1
			fs.write(f"{tabs}]{self.name}")	

	def get_dataframe(self,objects=True, membranes=True):
		full_name=[]
		ids = []
		labels = []
		parnets_ids = []
		parents_label=[]
		values = []
		types = []
		if self.parent :
			ids.append(self.id)
			labels.append(self.name)
			full_name.append(self.fcmn)
			if self.parent.id:
				parnets_ids.append(self.parent.id)
				parents_label.append(self.parent.name)
			else:
				parnets_ids.append("")
				parents_label.append("")
			values.append(self.repr_count)
			types.append(0)
		

		object_key_sorted = list(self.objects.keys())
		object_key_sorted.sort(key=lambda x :x.object)
		if len(object_key_sorted) > 0 :
			# ids.append(f"{membrane.id}.objects")
			# labels.append("Objects")
			# parnets_ids.append(membrane.id)
			# values.append(1)
			# colors.append("lightgray")
			for object in object_key_sorted :
				count = self.objects[object]
				count_value = count
				#count_value = count * membrane.total_repr_count
				#count_value =  membrane.repr_count
				if math.isinf(count):
					count_value = 1
				ids.append(f"{self.id}.{object}")
				labels.append(object.object)
				full_name.append(f"{self.fcmn}.{object.object}")
				#parnets_ids.append(f"{membrane.id}.objects")
				parnets_ids.append(self.id)
				parents_label.append(self.name)
				values.append(count_value)
				types.append(1)

		list_of_tuples = list(zip(types,parnets_ids,parents_label,ids,labels,full_name,values)) 
		df = pd.DataFrame(list_of_tuples, 
					columns=["type","parnet_id","parent_name","id","name","full_name","value"]) 
		for child_mem_key in self.childrens_group:
			for child_mem in self.childrens_group[child_mem_key]:
				child_df =  child_mem.get_dataframe()
				df = pd.concat([df,child_df],ignore_index=True)
		return df

	def __str__(self) -> str:
		if self.parent and self.parent != self.p_system.skin :
			if self.repr_count > 1 :
				return f"{self.parent.name}.{self.repr_count}*{self.name}"
			else :
				return f"{self.parent.name}.{self.name}"
		else :
			if self.repr_count > 1 :
				return f"{self.repr_count}*{self.name}"
			else :
				return f"{self.name}"

	def __repr__(self) -> str:
		if self.parent :
			if self.repr_count > 1 :
				return f"<[{self.repr_count}*{self.name}] {self.parent.name}>"
			else :
				return f"<[{self.name}] {self.parent.name}>"
		else :
			if self.repr_count > 1 :
				return f"<[{self.repr_count}*{self.name}]>"
			else :
				return f"<[{self.name}]>"

	@property
	def fcmn(self):
		if self.parent and self.parent != self.p_system.skin :
			return f"{self.parent.fcmn}.{self.name}"
		else :
			return f"{self.name}"


	@property
	def level(self):
		if self.parent :
			return self.parent.level + 1
		return 0 

	@property
	def total_repr_count(self):
		if self.parent :
			return self._repr_count * self.parent.total_repr_count
		return self._repr_count
	@property
	def repr_count(self):
		return self._repr_count
	@repr_count.setter
	def repr_count(self,new_count):
		## TODO  check new count
		self._repr_count = int(new_count)
		## update status
		if new_count < 0 :
			raise ValueError(f"Membrane count can not less than 0")
		self.membrane_status[PROPERTY_N] = new_count
		## in case of 0 we need to remove

class PSystem():
	'''
		PSystem contain the following :
		membranes definitions:
		* rules : all system rules
		* objects definitions :
		* main skin membrane
		* current statue : acutal membranes states stating from the skin 				

	'''
	_logger  = logging.getLogger("PSystem")

	def __init__(self, name=None) -> None:
		## load from yaml
		## System definiations 
		self._rules_definitions = [] 
		self._membranes_definitions = [] 
		self._objects_definitions : Dict[str,MembraneObject] = {}
		
		self._skin_membranes = []
		self.type = name ## name property

		## system instances and objects that is used in the simulation
		self.skin : Membrane = None
		
		self._membranes_map : Dict[str,Set[Membrane]] = {} 
		self._rules : List[Rule] = [] ## all system rules
		self._rules_map = {} ## all system rules map by id
		self._rules_membrane_map = {} # rules grouped by membrane
		## not included in this model/profile
		self._rejected_rules = [] # rules got rejected based on PPP 

		
		
		#self.step_index = 0
		
		## membrane that are going to change at the next cycle
		 
		
		if name:
			self._logger = logging.getLogger(f"PSystem:{self.type}")

############################### YAML Format V1 #########################################
	
	def _setup(self):
		"""
			there is some assumptions related to V1 for the format
		"""
		self._logger.debug("Setting up PSystem")

		self._logger.debug("Creating System Rules")
		for rule_definition in self._rules_definitions:
			rule_name = rule_definition["rule"]
			try:
				new_Rule = Rule.init_from_yaml_v1(rule_name,rule_definition,self)
				# new_Rule.interpret()
			except Exception as e:
				## can not handle this setting this rule;
				self._logger.error(f"Can not setup rule:{rule_name}")
				self._logger.error(f"Rule Cuasing the problem:\n {rule_definition}")
				raise InValidFormat(e) 
			## after we get the new rule add to

			## TODO :: rule selection for a profile based on PPP value of the rule
			## randomly selected 
			if new_Rule.is_selected_PPP() :
				self._rules.append(new_Rule)

				self._rules_map[rule_name] = new_Rule
				## TODO :: Update to handle multiple input membranes 
				if not new_Rule.membrane in self._rules_membrane_map:
					self._rules_membrane_map[new_Rule.membrane] = []
				self._rules_membrane_map[new_Rule.membrane].append(new_Rule)
			else :
				self._rejected_rules.append(new_Rule)

		
		

		self._logger.debug("Creating System Skin Membrane State")
		skin_definition = {
			PROPERTY_MEMBRANES:self._skin_membranes,
			PROPERTY_MEMBRANE:self.type
		}
		# skin_definition = self.get_membrane_definition(system_membrane)
		skin_definition = PSystem._normalize_membrane_definiations(skin_definition)
		self.skin =  Membrane.init_from_def(skin_definition,self)
		self.add_membrane(self.skin)	

		
			# for membrane_yaml_obj in membranes_yaml_objs:
				
			# 	name_membrane=(list((membrane_yaml_obj.keys())))[0]
			# 	type_membrane=(list((membrane_yaml_obj.values())))[0]['type']
			# 	new_membrane = Membrane.init_from_yaml(name_membrane,type_membrane,membrane_yaml_obj,new_system)
			# 	new_system._membranes.append(new_membrane)
			  
			# 	## dict impl ...
			# 	new_system._membranes_hash[new_membrane.name] = new_membrane
		#new_system.get_membranes_parent()
		#new_system.creat_number_of_instance()
	#@staticmethod

	@classmethod
	def _normalize_membrane_definiations(cls,membrane_def):
		"""
		membrane definiations is a simplifed form of a membrane state
		only contains objects and a list of child membranes and counts 
		"""
		if PROPERTY_OBJECTS in membrane_def :
			if membrane_def[PROPERTY_OBJECTS] :
				membrane_def[PROPERTY_OBJECTS] = unpackListAsDict(membrane_def[PROPERTY_OBJECTS])
				## fix no explict number 
				for o_key in membrane_def[PROPERTY_OBJECTS]:
					obj = membrane_def[PROPERTY_OBJECTS][o_key]
					if obj : # object could be None by mistake from yaml file
						if not isinstance(obj,dict):
							unresolved_value = unresolved_value_to_dict(obj)
							membrane_def[PROPERTY_OBJECTS][o_key] = unresolved_value
						obj = membrane_def[PROPERTY_OBJECTS][o_key]
						if PROPERTY_N in obj:
							if obj[PROPERTY_N] == INF_SYMBOL:
								obj[PROPERTY_N] = math.inf
					else :
						membrane_def[PROPERTY_OBJECTS][o_key] = {}
					

			else :
				del membrane_def[PROPERTY_OBJECTS]
		## similar to rule hand sides but without nested strucutre 
		if PROPERTY_MEMBRANES in membrane_def :
			if membrane_def[PROPERTY_MEMBRANES] :
				#rules_in_membranes = new_state[PROPERTT_MEMBRANES].copy()
				unpackList(membrane_def[PROPERTY_MEMBRANES],PROPERTY_MEMBRANE)
				for membrane in membrane_def[PROPERTY_MEMBRANES] :
					if UNRESOLVED_MAPPED_VALUE in membrane :
						unresolved_value = membrane[UNRESOLVED_MAPPED_VALUE]
						unresolved_value = unresolved_value_to_dict(unresolved_value)
						if unresolved_value :
							membrane.update(unresolved_value)
							del membrane[UNRESOLVED_MAPPED_VALUE]
					## handle nested structure
					membrane = cls._normalize_membrane_definiations(membrane)
			else :
				del membrane_def[PROPERTY_MEMBRANES]
		return membrane_def	
	@classmethod
	def init_from_yaml_v1(cls,from_yaml_obj) -> 'PSystem'  :
		cls._logger.debug("init PSystem from a yaml file V1")
		default_name = "system"
		new_system  = None
		##  validate that it has a system property
		system_object = from_yaml_obj["system"]
		if "type" in system_object:
			##  set name
			default_name = system_object["type"]
		new_system = cls(name=default_name)
		if PROPERTY_OBJECTS in system_object:
			# optional objects definitions
			cls._logger.debug("Initializing objects definitions")
			objects_yaml_def = system_object[PROPERTY_OBJECTS]
			for obj_key in objects_yaml_def:
				print(obj_key)
				new_obj = MembraneObject(obj_key,objects_yaml_def[obj_key])
				new_system._objects_definitions[obj_key] = new_obj
		else :
			new_system.objects_definitions = {}

		if PROPERTY_MEMBRANES in system_object:
			cls._logger.debug("Initializing Membranes definitions")
			## avoid modify object from yaml file in case we need it later
			membranes_yaml_def = copy.deepcopy(system_object[PROPERTY_MEMBRANES])
			nested_structure = False
			if len(membranes_yaml_def) == 1:
				## if we have only one membrane we can have a nested structure
				nested_structure = True
			new_system._membranes_definitions = unpackListAsDict(membranes_yaml_def,PROPERTY_MEMBRANE)
			
			for membrane_key in new_system._membranes_definitions :
				membrane_def = new_system._membranes_definitions[membrane_key]
				try :
					## DEBUG ONLY
					# if membrane_key == "CS" :
					# 	print(membrane_key)
					membrane_def = cls._normalize_membrane_definiations(membrane_def)
					cls._logger.debug(f"Membrane: {membrane_key:>20} = {cls.membraneDefiniationToStr(membrane_def,True)}")
				except  Exception as e:
					cls._logger.error(f"Can not process Membrane {membrane_key}")
					raise e
		else:
			## in case no membrane define 
			raise InValidFormat("The system must define membranes list")
		
		if PROPERTY_RULES in system_object:
			cls._logger.debug("Initializing Rules definitions")
			rules_yml_objs = system_object[PROPERTY_RULES]
			unpackList(rules_yml_objs,"rule")
			if rules_yml_objs:
				new_system._rules_definitions = rules_yml_objs
		else:
			cls._logger.warn(f"PSystem {default_name} does not contains any rules definitions")



		# PROPERTY_SKIN
		
		if PROPERTY_SKIN in system_object:
			if isinstance(system_object[PROPERTY_SKIN],str):
				new_system._skin_membranes.append(system_object[PROPERTY_SKIN])
			else:
				new_system._skin_membranes.extend( system_object[PROPERTY_SKIN])
			for skin_membrane in new_system._skin_membranes:
				if not isinstance(skin_membrane,str):
					raise InValidFormat(f"Invalid value provided in skin membrane list : {skin_membrane}")
		if len(new_system._skin_membranes) == 0 :
			new_system._skin_membranes = cls.__identify_root_membranes(new_system._membranes_definitions)

		for skin_membrane in new_system._skin_membranes:
			if not skin_membrane in new_system._membranes_definitions:
				## we must have a skin membrane
				raise InValidFormat(f"The system can not find  skin membranes : {skin_membrane} ")
		new_system._setup()
		
		return new_system

	def is_skin_membrane(self,membrane : Membrane) :
		for _mem_def in self._skin_membranes:
			if _mem_def[PROPERTY_MEMBRANE] == membrane.name :
				return True
		return False


	@classmethod
	def __expand_levels(cls,levels,mem_def,current_level):
		"""
		guess root levels for membranes
		"""
		if PROPERTY_MEMBRANES in mem_def :
			for mem_def in mem_def[PROPERTY_MEMBRANES]:
				mem_key = mem_def[PROPERTY_MEMBRANE]
				if mem_key in levels:
					levels[mem_key] = max(levels[mem_key],current_level+1)
				else :
					levels[mem_key] = current_level+1
				cls.__expand_levels(levels,mem_def,current_level+1)

	@classmethod
	def __identify_root_membranes(cls,membranes_definitions):
		levels = {}
		for mem_key in membranes_definitions:
			mem_def = membranes_definitions[mem_key]
			if not mem_key in levels:
				levels[mem_key] = 1
			cls.__expand_levels(levels,mem_def,levels[mem_key])
		return [_m for _m in levels if levels[_m] == 1 ]
	
	@classmethod
	def save_to_yaml_v1(cls,pSystem,simple_format=True):
		def object_definition_to_format(obj_def):
			object_format = {}
			if isinstance(obj_def,dict):
				for def_key in obj_def :
					## custom case of keys
					if def_key == PROPERTY_N and math.isinf(obj_def[def_key]) :
						object_format[def_key] = INF_SYMBOL
					elif simple_format and def_key == PROPERTY_N and obj_def[def_key] == 1 :
						# do not add number it is the default value
						pass
					else :
						object_format[def_key] = obj_def[def_key]
					
					pass
			if simple_format:
				if len(object_format) == 1 :
					n0_key = list(object_format.keys())[0]
					if n0_key == PROPERTY_N and  object_format[PROPERTY_N] == 1:
						return None
					if n0_key == PROPERTY_ACTION or n0_key == PROPERTY_N :
						return object_format[n0_key]
			
			return object_format

		def membrane_definition_to_format(membrane_def, membrane_name=None):
			membrane_format = {}
			_objects_ = None
			_membranes_ = None
			for def_key in membrane_def:
				if simple_format and def_key == PROPERTY_N and membrane_def[def_key] == 1 :
					# do not add number it is the default value
					pass
				elif def_key == PROPERTY_MEMBRANE:
					## do not do anything here, key/name is stored ouside
					pass
				elif def_key == PROPERTY_OBJECTS:
					_objects_ = membrane_def[def_key]
					membrane_format[PROPERTY_OBJECTS] = []
					for _obj_key in _objects_:
						_obj_def = object_definition_to_format(_objects_[_obj_key])
						if _obj_def:
							membrane_format[PROPERTY_OBJECTS].append({_obj_key: _obj_def})
						else:
							membrane_format[PROPERTY_OBJECTS].append(_obj_key)
				elif def_key == PROPERTY_MEMBRANES:
					_membranes_ = membrane_def[PROPERTY_MEMBRANES]
					membrane_format[PROPERTY_MEMBRANES] = []
					for child_membrane in _membranes_:
						child_membrane_name = child_membrane[PROPERTY_MEMBRANE]
						child_membrane_def = membrane_definition_to_format(child_membrane)
						if child_membrane_def:
							membrane_format[PROPERTY_MEMBRANES].append(
                                                    {child_membrane_name: child_membrane_def}
                                                )
						else:
							membrane_format[PROPERTY_MEMBRANES].append(child_membrane_name)
				else:
					## TODO :: make sure that is a copy just in case we modify it later
					membrane_format[def_key] = membrane_def[def_key]

			if simple_format:
				if len(membrane_format) == 1:
					n0_key = list(membrane_format.keys())[0]
					if n0_key == PROPERTY_ACTION or n0_key == PROPERTY_N:
						return membrane_format[n0_key]

			return membrane_format

		system_config = {}
		
		## system will be writen from the definiation we have
		system_config[PROPERTY_TYPE] = pSystem.type
		system_config[PROPERTY_FORMAT] = INPUT_FORMAT_V1
		system_config[PROPERTY_OBJECTS] = copy.deepcopy(pSystem._objects_definitions)
		system_config[PROPERTY_SKIN] = pSystem._skin_membrane
		system_config[PROPERTY_MEMBRANES] = []
		for m_key in pSystem._membranes_definitions:
			membrane_def = pSystem._membranes_definitions[m_key]
			system_config[PROPERTY_MEMBRANES].append(
                            {
                                m_key: membrane_definition_to_format(
                                    membrane_def, m_key)
                            }
                        )
		import yaml
		yaml.dump({"system":system_config}, 
			open("data.yml","w"), 
			default_flow_style=False , 
			allow_unicode=True,sort_keys=False)
		
	def write_rules(self,output_filename):
		use_color(False)
		with open(output_filename,"w") as output_file:
			output_file.write("membranes:\n\n")
			output_file.write(self.skin.get_str_status(False))
			
			_rules = []
			## TODO :: detected duplicate rules
			_rules.extend(self._rules)
			_rules.extend(self._rejected_rules)
			_rules.sort(key=lambda x : x.name)
			output_file.write("\n\n## All System Rules\n")
			output_file.write("rules:\n")
			for rule in _rules:
				output_file.write(rule.__str__())
				output_file.write("\n")
			pass
		use_color(True)
	def sort_rules(self):
		'''
			sort rules to simulate a nondeterministic system
		'''
		## randomnize the order of self._rules
		# multisort(self._rules, (("RPI",False) , ("membrane_level",True),  ("membrane",True)))
		random.shuffle(self._rules)
		# multisort(self._rules, (("RPI",False) , ("membrane_level",True)))
		multisort(self._rules, (("RPI",False) , ))
		# print("stop")
		pass
#########################################################################################

	@classmethod
	def membraneDefiniationToStr(cls,membrane_def,include_itself=False):
		membrane_os_str = ""
		membrane_ms_str = ""

		if PROPERTY_OBJECTS in membrane_def:
			for o_key in membrane_def[PROPERTY_OBJECTS] :
				obj = membrane_def[PROPERTY_OBJECTS][o_key] 
				n = 1
				if PROPERTY_N in obj:
					n = obj[PROPERTY_N]
				if n == math.inf :
					n = INF_SYMBOL
				membrane_os_str += f" {Fore.GREEN}{n}{Fore.RESET}{Fore.BLUE}{o_key}{Fore.RESET},"

		membrane_os_str = membrane_os_str.strip() 
		if len(membrane_os_str) > 0 :
			if membrane_os_str[-1] == ",":
				membrane_os_str = membrane_os_str[:-1]
		membrane_os_str = membrane_os_str.strip() 

		if PROPERTY_MEMBRANES in membrane_def:
			for membrane in membrane_def[PROPERTY_MEMBRANES]:
				membrane_num_str = ""
				membrane_name = membrane[PROPERTY_MEMBRANE]
				n = 1
				if PROPERTY_N in membrane:
					n = membrane[PROPERTY_N]
				membrane_num_str = f"{Fore.MAGENTA}{n}{Fore.RESET}"
				membrane_hs_str = cls.membraneDefiniationToStr(membrane)
				#if membrane_hs_str:
				#	membrane_hs_str = f"[{membrane_hs_str}]"
				membrane_ms_str += f"{membrane_num_str}[{membrane_hs_str}]{Fore.RED}{membrane_name}{Fore.RESET} "
		membrane_ms_str = membrane_ms_str.strip()
		

		
		membrane_str = ""
		if membrane_os_str and membrane_ms_str :
			membrane_str = f"{membrane_os_str} {membrane_ms_str} "
		if not membrane_os_str and  membrane_ms_str :
			membrane_str =  f" {membrane_ms_str} "
		if membrane_os_str and not membrane_ms_str :
			membrane_str = f"{membrane_os_str}"
		if include_itself:
			membrane_name = membrane_def[PROPERTY_MEMBRANE]
			return  f"[{membrane_str}]{Fore.RED}{membrane_name}{Fore.RESET}"
		return membrane_str
	
	###############################################
	def get_membrane_definition(self,membrane_key, orCreate = False):
		try :
			return self._membranes_definitions[membrane_key]
		except :
			if orCreate:
				return {PROPERTY_MEMBRANE:membrane_key,PROPERTY_TYPE:membrane_key}
			return None
	
	def getObject(self,obj_key):
		if not obj_key in self._objects_definitions:
			self._objects_definitions[obj_key] = MembraneObject(obj_key)
		return self._objects_definitions[obj_key]
	

	def remove_membrane(self,membrane : 'Membrane'):
		"""
		remove a membrane from  membranes_map
		"""
		## TODO Validate and check
		self._membranes_map[membrane.name].remove(membrane)

	def add_membrane(self,membrane : 'Membrane'):
		"""
			add membrane to the map for faster access to it
		"""
		
		if not membrane.name in self._membranes_map:
			self._membranes_map[membrane.name] = set()
		self._membranes_map[membrane.name].add(membrane)


	def get_membrane(self,membrane_name):
		"""
			get a membrane from the map, if this is not updated it would not work
			retrun none if it does not exist
		"""
		if membrane_name in self._membranes_map:
			return list(self._membranes_map[membrane_name] )
		return None



	def __str__(self) -> str:
		'''
			override method to print the system 
		'''
		_str_rep = f"PSystem: {self.type}"
	   

		for membrane in self._membranes:
			_str_rep = f"{_str_rep}\n##\n{membrane}"
		_str_rep = f"{_str_rep}\n\n#Rules#\n"
		for rule in self._rules:
			_str_rep = f" {_str_rep}\n{rule}"
		return _str_rep

	def __repr__(self) -> str:
		return self.__str__()
	def print_status(self):
		## name ->> status
		## rulues true
		pass






#############
#### plot 
import pandas as pd 
import plotly.graph_objects as go
def get_plot_df(membrane : Membrane):
    ids = []
    labels = []
    parnets_ids = []
    values = []
    colors= []
    texts = []
    if membrane.parent :
        ids.append(membrane.id)
        labels.append(membrane.name)
        if membrane.parent.id:
            parnets_ids.append(membrane.parent.id)
        else:
            parnets_ids.append("")
        values.append(membrane.repr_count)
        colors.append("lightblue")
        texts.append("")
    # else:
    #     if membrane.id:
    #         ids.append(membrane.id)
    #     else:
    #         ids.append(membrane.name)
    #     labels.append(membrane.name)
    #     parnets_ids.append("")
    #     values.append(membrane.repr_count)

    object_key_sorted = list(membrane.objects.keys())
    object_key_sorted.sort(key=lambda x :x.object)
    if len(object_key_sorted) > 0 :
        # ids.append(f"{membrane.id}.objects")
        # labels.append("Objects")
        # parnets_ids.append(membrane.id)
        # values.append(1)
        # colors.append("lightgray")
        for object in object_key_sorted :
            count = membrane.objects[object]
            count_value = count
            #count_value = count * membrane.total_repr_count
            #count_value =  membrane.repr_count
            if math.isinf(count):
                count_value = 1
            ids.append(f"{membrane.id}.{object}")
            labels.append(object.object)
            #parnets_ids.append(f"{membrane.id}.objects")
            parnets_ids.append(membrane.id)
            values.append(count_value)
            colors.append("red")
            if object in membrane.p_system._objects_definitions:
                texts.append( membrane.p_system._objects_definitions[object].desc)
            else:
                texts.append("Obj Desc")
    list_of_tuples = list(zip(ids,labels,parnets_ids,values,colors,texts)) 
    df = pd.DataFrame(list_of_tuples, 
                  columns=["ids","labels","parnets_ids","values","colors","texts"]) 
    for child_mem_key in membrane.childrens_group:
        for child_mem in membrane.childrens_group[child_mem_key]:
            child_df =  get_plot_df(child_mem)
            df = pd.concat([df,child_df],ignore_index=True)
            # ids.extend(child_ids)
            # parnets_ids.extend(child_parnets_ids)
            # labels.extend(child_labels)
            # values.extend(child_values)
            # colors.extend(child_colors)
            # texts.extend(child_texts)
    return df


def plot_membrane (membrane : Membrane, outputname=None):
	df = get_plot_df(membrane)
	fig = go.Figure(go.Treemap(
        ids=df['ids'],
        labels=df['labels'],
        parents=df['parnets_ids'],
        values=df['values'],
        text=df['texts'],
        ## pathbar_textfont_size=15,
        marker=dict(
            colors=df['colors'],
            cornerradius=5
            ),
        root_color="lightgrey",

        maxdepth=5
        ))

	fig.update_layout(
        # # uniformtext=dict(minsize=10, mode='hide'),
        margin = dict(t=50, l=25, r=25, b=25))
	if outputname:
		fig.write_html(outputname)
	else:
		fig.show()




#################################################################