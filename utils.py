import os, sys, re, r2pipe, json, argparse

# This contains a mapping of op_type returned by radare2 to the 
# type of instructions like nop, control, transfer, arithmetic, etc.
# Following abbreviations are used here:
# N : Nop instructions
# C : Control instructions
# U : Unknown instructions
# T : Transfer instructions
# L : Logical instructions
# S : System calls
# A : Arithmetic instructions
op_type_to_category = { 0: 'N',
                        1: 'C',
                        2: 'C',
                        3: 'C',
                        4: 'C',
                        5: 'C',
                        6: 'U',
                        7: 'U',
                        8: 'N',
                        9: 'T',
                        10: 'U',
                        11: 'S',
                        12: 'T',
                        13: 'T',
                        14: 'T',
                        15: 'L',
                        16: 'L',
                        17: 'A',
                        18: 'A',
                        19: 'T',
                        20: 'A',
                        21: 'A',
                        22: 'A',
                        23: 'A',
                        24: 'A',
                        25: 'A',
                        26: 'L',
                        27: 'L',
                        28: 'L',
                        29: 'L',
                        30: 'L',
                        31: 'T',
                        32: 'T',
                        33: 'T',
                        34: 'T',
                        35: 'A',
                        36: 'A',
                        37: 'T',
                        38: 'A',
                        39: 'C',
                        40: 'U',
                        41: 'U',
                        42: 'U',
                        43: 'U',
                        44: 'A',
                        45: 'L',
                        46: 'U',
                        47: 'U'}


# Returns the paths of all folders which either contains header files
# or its subfolder contains any of the header files
def find_all_headers_folders(folder_path):
    headers_folder_set = set()
    for root, _, files in os.walk(folder_path):
        for x in files:
            if x.endswith(".h") or x.endswith(".hpp"):
                # Add this folder and its parent folders to the result set
                root_folders = root.split('/')
                for i in range(1, len(root_folders) + 1):
                    headers_folder_set.add("/".join(root_folders[:i]))
    return list(headers_folder_set)


# Given the path of source file and the list of all source folders (in which, all the headers used in the
# source file can be found), we compile the source code to object file and save that object
# file by the name of "object_file"
def compile_to_object_file(source_file_path, headers_folder_list, extra_flags = "", debug_mode = False):
    # Generate command to compile functions
    cmd = "g++ -g -c %s %s %s -o object_file 2>>compile_error_trace" % (extra_flags, " -I".join(headers_folder_list), source_file_path)
    if debug_mode:
        print(cmd)
    # Execute
    return os.system(cmd)


# Retrieve the list of all non-static functions which is present in the source file along with its definition
def get_func_list(source_file_path):
    # Getting function names
    function_list_raw = os.popen("ctags -x --c++-kinds=f \"%s\"" % source_file_path).read().split('\n')
    function_list = []
    all_function_with_def_set = set()
    # We are removing static function 
    for f in function_list_raw:
        if ('static' not in f):
            # This is a check for empty lines
            try:
                function_list.append(f.split()[0])
            except:
                pass
        try:
            all_function_with_def_set.add(f.split()[0])
        except:
            pass
    return list(all_function_with_def_set)


# Save decompiled functions
def save_decompiled_functions(object_file_path, func_list_from_src):
    # Retrieve the decompiled assembly for all functions
    r2_pipe = r2pipe.open("object_file", flags=['-2'])
    _ = r2_pipe.cmd("aab")
    _ = r2_pipe.cmd("aac")
    
    decompiled_functions_list = list()
    func_to_decompiled_dict = dict()
    funcs = r2_pipe.cmdj("aflj")
    for func in funcs:
        f = func['offset']
        decompiled_function = r2_pipe.cmd('pdf @%s' % f)
        decompiled_functions_list.append(decompiled_function)
        for f2 in func_list_from_src:
            if ";-- %s" % f2 in decompiled_function:
                func_to_decompiled_dict[f2] = decompiled_function
            
    json.dump(func_to_decompiled_dict, open('decompiled_functions.json', 'w'), indent=4)
    print("Results are saved in decompiled_functions.json")


# Given r2pipe and function address, it return the edges present in the function 
# in the following format [(basic_block_1_address, basic_block_2_address), (...), ...]
def get_function_edges(function_address, r2_pipe):
    edge_info = r2_pipe.cmd("ags @%s" % function_address).split('\n')
    edges = []
    for x in edge_info:
        if x[14:16] == '->':
            edges.append([int(x[2:12], 16), int(x[18:28], 16)])
    return edges


# Input : path of the binary file and list of functions present in the
# corresponding source code of the binary
# 
# Output : {"function_name" : {"offset" : xyz, "features" : [numerical features, structural features]}}
# Numerical features format : [nbbs, outdegree, nlocals, edges, nargs, T, A, L, All]
# Structural Feature format : [nbbs, edges, list of vertices, list of edges, characteristic list]
# Characteristics feature format : [arith_instr_cnt, call_cnt, instr_cnt, log_instr_cnt, trans_instr_cnt, strings_cnt, numeric_cnt]
def get_func_nf_sf_one_file(file_path, func_list_from_src):
    result_dict = dict()
    r2_pipe = r2pipe.open(file_path, flags=['-2'])
    _ = r2_pipe.cmd("aab")
    _ = r2_pipe.cmd("aac")
    funcs = r2_pipe.cmdj('aflj')
    if funcs is None:
        return result_dict
    for func in funcs:
        if len(func) < 1:
            continue
        match_found = False
        function_name = ""
        f = func['offset']
        decompiled_function = r2_pipe.cmd('pdf @%s' % f)
        for f2 in func_list_from_src:
            if ";-- %s" % f2 in decompiled_function:
                function_name = f2
                match_found = True
        if not match_found:
            continue
        # Extract numerical features
        # Numerical features format : [nbbs, outdegree, nlocals, edges, nargs, T, A, L, All]
        counter = {'T' : 0, 'All' : 0, 'A' : 0, 'L' : 0}
        function_basic_blocks = r2_pipe.cmdj("agj @%s" % str(f))
        if function_basic_blocks is None:
            continue
        if len(function_basic_blocks) >= 1:
            for block in function_basic_blocks[0]['blocks']:
                for opcode in block['ops']:
                    counter['All'] += 1
                    if 'type_num' in opcode:
                        if (int(opcode['type_num']) % 64) in op_type_to_category:
                            tmp_catagory = op_type_to_category[int(opcode['type_num']) % 64]
                            if tmp_catagory == 'N': # We are not counting null instructions
                                counter['All'] -= 1
                            if tmp_catagory in counter:
                                counter[tmp_catagory] += 1
        numerical_feature = [
            func['nbbs'],
            func['outdegree'],
            func.get('nlocals',0),
            func['edges'],
            func.get('nargs',0),
            counter['T'],
            counter['A'],
            counter['L'],
            counter['All']
        ]
        # Extract structural feature
        # Feature format : [nbbs, edges, list of vertices, list of edges, characteristic list]
        structural_feature = [
            func['nbbs'],
            func['edges'],
            [],
            [],
            []
        ]
        basic_block_list = []
        basic_block_features = []
        if len(function_basic_blocks) >= 1:
            for block in function_basic_blocks[0]['blocks']:
                # Get the address of basic block and add it to the list
                block_offset = int(block['offset'])
                basic_block_list.append(block_offset)
                # Store the other features of basic block
                counter_block = {'T' : 0, 'All' : 0, 'A' : 0, 'L' : 0}
                for opcode in block['ops']:
                    counter['All'] += 1
                    if 'type_num' in opcode:
                        if (int(opcode['type_num']) % 64) in op_type_to_category:
                            tmp_catagory = op_type_to_category[int(opcode['type_num']) % 64]
                            if tmp_catagory == 'N': # We are not counting null instructions
                                counter['All'] -= 1
                            if tmp_catagory in counter_block:
                                counter_block[tmp_catagory] += 1
                # Characteristics of each basic block
                # Feature format : [arith_instr_cnt, call_cnt, instr_cnt, log_instr_cnt, trans_instr_cnt, strings_cnt, numeric_cnt]
                feature = [counter['A'], 0, counter['All'], counter['L'], counter['T'], 0, 0]
                # Create feature dictionary for each basic block
                basic_block_features.append(feature)
        structural_feature[2] = basic_block_list
        structural_feature[4] = basic_block_features
        edge_list = get_function_edges(str(f), r2_pipe)
        edge_list = [[x,y] for x,y in edge_list if (x in basic_block_list and y in basic_block_list)]
        structural_feature[3] = edge_list
        structural_feature[0] = len(basic_block_list)
        structural_feature[1] = len(edge_list)
        result_dict[function_name] = dict()
        result_dict[function_name]["offset"] = func['offset']
        result_dict[function_name]["features"] = [numerical_feature, structural_feature]
    r2_pipe.quit()
    return result_dict


# Requirements:
# * Extract nf and sf of all the functions present in all the files
#   * Extract nf and sf from one file
#   * Iterate above for all the files
#   

# Test function
if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Function Specific Compilation')
    parser.add_argument('input_source_file', type=str, help='Path of the input source file')
    parser.add_argument('source_folder', type=str, help='Path of the source folder')
    args = parser.parse_args()
    cpp_file_path = args.input_source_file
    codebase_folder_path = args.source_folder
    
    # Get all folders (with their parent folders) which contains their header files
    headers_folder_list = find_all_headers_folders(codebase_folder_path)

    # Compile to get object file
    compile_to_object_file(cpp_file_path, headers_folder_list)

    # Retrieve function list from source code
    func_list_from_src = get_func_list(cpp_file_path)

    # Extract nf and sf
    tmp = get_func_nf_sf_one_file("object_file", func_list_from_src)
    json.dump(tmp, open("features.json", 'w'), indent=4)
