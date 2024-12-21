#! /usr/bin/env python3

import argparse
import sys
import os
import configparser
import logging

import yaml

from module.helper import PROPERTY_MEMBRANES
from module.parse_rules import parse_ini_to_yml
from module.simulator import PSystem, Rule, plot_membrane
logging.basicConfig(
    format='[%(asctime)s] %(levelname)-8s  [%(name)s] %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('main')
def extract_path_and_prefix(output_arg):
    """
    Extract path and prefix from output argument
    Example: 'path/to/prefix' -> ('path/to', 'prefix')
    Example: 'prefix' -> ('', 'prefix')
    Example: '.' -> ('', 'output')  # Default prefix when only path is given
    """
    if output_arg == '.':
        return '', 'output'
        
    output_path = os.path.dirname(output_arg)
    file_prefix = os.path.basename(output_arg)
    
    # If file_prefix is empty (e.g., "path/to/"), use default prefix
    if not file_prefix:
        file_prefix = 'output'
        
    return output_path, file_prefix
def network_plot(psystem, output_filename):
    """
    Plot the network of the membrane
    """
    system_rules = list(psystem._rules)
    system_rules.extend(psystem._rejected_rules)

    source_rule : Rule 
    target_rule : Rule

    source = []
    target = []
    nodes = set()
    from pyvis.network import Network
    nt = Network('2000px', '2000px',directed =True)

    for target_rule in system_rules:
        
        if isinstance(target_rule.output,str):
            continue
        
        for io in target_rule.input_membranes_map:
            io_def = target_rule.input_membranes_map[io]
            membrane_name = io_def['name']
            # print(io_def['name'])
            if 'objects' in  io_def['input_node']:
                for obj in io_def['input_node']['objects']:
                    # print(obj)
                    source_node = f"{membrane_name}.{obj}"
                    target_node = f"{target_rule.name}"
                    if not target_node in nodes:
                        nt.add_node(target_node,color='#FF0000',shape="box")
                    if not source_node in nodes:
                        nt.add_node(source_node,color='blue',shape="triangle")
                    nt.add_edge(source_node,target_node,color="red")
                    source .append(source_node)
                    target.append(f"{target_rule.name}")
            else:
                if not 'membranes' in io_def['input_node']:
                    source.append(membrane_name)
                    target_node = f"{target_rule.name}"
                    if not target_node in nodes:
                        nt.add_node(target_node,color='#FF0000',shape="box")
                    source_node = membrane_name
                    if not source_node in nodes:
                        nt.add_node(source_node,color='green',shape="dot")
                    nt.add_edge(source_node,target_node,color="red")
                    target.append(f"{target_rule.name}")
        
        output_membranes_list = Rule._get_all_membranes_name(target_rule.output[PROPERTY_MEMBRANES])
        for io_def in output_membranes_list:
            
            membrane_name = io_def['name']
        
            if 'objects' in  io_def['input_node']:
                for obj in io_def['input_node']['objects']:
                    source_node = f"{target_rule.name}"
                    target_node = f"{membrane_name}.{obj}"
                    if not source_node in nodes:
                        nt.add_node(source_node,color='#FF0000',shape="box")
                    if not target_node in nodes:
                        nt.add_node(target_node,color='blue',shape="triangle")
                    nt.add_edge(source_node,target_node,color="blue")
                    target.append(f"{membrane_name}.{obj}")
                    source.append(f"{target_rule.name}")
            else:
                if not 'membranes' in io_def['input_node']:
                    source_node = f"{target_rule.name}"
                    target_node = membrane_name
                    if not source_node in nodes:
                        nt.add_node(source_node,color='#FF0000',shape="box")
                    if not target_node in nodes:
                        nt.add_node(target_node,color='green',shape="dot")
                    nt.add_edge(source_node,target_node,color="blue")
                    target.append(membrane_name)
                    source.append(f"{target_rule.name}")
        # print("-----")
    nt.show_buttons(filter_=['physics'])
    nt.show( output_filename,notebook=False)


def process_input(input_file, output_arg):
    """
    Process the input text/ini file and generate output with the given prefix
    """
    try:
        # Extract path and prefix
        output_path, file_prefix = extract_path_and_prefix(output_arg)
        
        # Create output directory if it doesn't exist and path is provided
        if output_path and not os.path.exists(output_path):
            os.makedirs(output_path)
        
        
        # TODO: Add processing logic here
        # Use output_path and file_prefix for generating output files
        # Example: full_path = os.path.join(output_path, f"{file_prefix}_result.txt")
        output_filename = os.path.join(output_path, f"{file_prefix}.yml")
        input_yaml_filename= parse_ini_to_yml(input_file, output_filename)
        with open(input_yaml_filename, encoding='utf8') as file:
            logger.info("Reading yaml file")
            psystem_config = yaml.load(file, Loader=yaml.FullLoader)
            logger.debug("init PSystem object from yaml file")
            pSystem = PSystem.init_from_yaml_v1(psystem_config)
            html_filename = os.path.join(output_path, f"{file_prefix}.html")
            logger.info(f"Plotting membrane to {html_filename}")
            plot_membrane(pSystem.skin,html_filename)
            network_filename = os.path.join(output_path, f"network_{file_prefix}.html")
            logger.info(f"Plotting network to {network_filename}")
            network_plot(pSystem,network_filename)
        return True
    except Exception as e:
        print(f"Error processing input: {str(e)}", file=sys.stderr)
        return False

def main():

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Process text/ini input and generate output files'
    )
    
    # Add required arguments
    parser.add_argument(
        '--input',
        required=True,
        help='Input text/ini file path'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output file prefix'
    )
    
    # Parse arguments
    args = parser.parse_args()
    logger.info(f"Processing input file: {args.input}")
    logger.info(f"Output prefix: {args.output}")
    # Process the input
    success = process_input(args.input, args.output)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()