import os
import sys
import r2pipe
import pickle
import numpy as np
import subprocess
from collections import Counter

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


# It will create a tmp folder in the current directory and extract deb file inside that
# then, it will return the list of the paths of all elf files present in the tmp folder
def get_elf_files_list(deb_filename):
    # Extract deb file
    if os.path.isdir("tmp"):
        os.system("rm -rf tmp")
    os.system("dpkg -x \"%s\" tmp" % deb_filename)

    # Search for elf files in the extracted folder
    foldername = "tmp"
    elf_files = []
    for root, _, files in os.walk(foldername):
        for filename in files:
            filepath = root + "/" + filename
            cmd = "file \"%s\"" % filepath
            cmd_out = subprocess.check_output(cmd, shell=True)
            if "ELF" in cmd_out.decode():
                elf_files.append(filepath)
    return elf_files


# Given the r2pipe and the address of function this, function will extract the following features 
# from the function 
# 1. nbbs - Number of basic blocks
# 2. outdegree - Number of function calls
# 3. nlocals - Number of local variables in the function
# 4. edges - Number of edges between the basic blocks of function
# 5. nargs - Number of arguments of function
# 6. T - Number of transfer instructions
# 7. A - Number of arithmetic instructions
# 8. L - Number of Logical instructions
# 9. All - Total number of instructions
def get_function_features(function_address, r2_pipe):
    out_dict = dict()
    function_info = r2_pipe.cmdj("afij @%s" % function_address)[0]
    if function_info is None:
        return 
    for x in ['nbbs', 'outdegree', 'nlocals', 'edges', 'nargs']:
        out_dict[x] = function_info.get(x, 0)

    counter = {'T' : 0, 'All' : 0, 'A' : 0, 'L' : 0}

    function_basic_blocks = r2_pipe.cmdj("agj @%s" % function_address)
    if len(function_basic_blocks) >= 1:
        for block in function_basic_blocks[0]['blocks']:
            for opcode in block['ops']:
                counter['All'] += 1
                if 'type_num' in opcode:
                    if (int(opcode['type_num']) % 64) in op_type_to_category:
                        tmp_catagory = op_type_to_category[int(opcode['type_num']) % 64]
                        if tmp_catagory in counter:
                            counter[tmp_catagory] += 1
    
    for x in counter:
        out_dict[x] = counter[x]

    return out_dict


# This will create a KNN model so that we can find neighbors around the query point
## Creating new object : knn_model = KNN_Model(Mapping_input)
# Mapping Input : it takes a function to feature dictionary of the following format
# {
#   "func1" : {
#                 "feature1" : value1,
#                 "feature2" : value2,
#                 ...
#             }
#   "func2" : {
#                 ...
#             }
#   ...
# }
## Quering : query_output = knn_model.get_neighbors(Query_input)
# Query Input : it takes a dictionary of features in the following format
# {
#     "feature1" : value1,
#     "feature2" : value2,
#     ...
# }
# Query Output : it returns a list of functions in the following format
# ['func1name', 'func2name', ... ]
class KNN_Model:
    def dist(self, a, b):
        M = self.dist_metric
        d = 0
        n = len(a)
        for i in range(n):
            t = 0
            for j in range(n):
                t += a[j] * M[i][j]
            d += t * b[i]
        return d

    def __init__(self, function_to_features):
        self.function_list = list(function_to_features.keys())
        self.feature_list = ['nbbs', 'outdegree', 'nlocals', 'edges', 'nargs', 'T', 'A', 'L', 'All']
        self.feature_matrix = [[function_to_features[y][x] for x in self.feature_list] for y in self.function_list]
        self.dist_metric = pickle.load(open('distance_metric.pickle', 'rb'))
        # Creating KNN model
        from sklearn.neighbors import KNeighborsClassifier
        self.knn_model = KNeighborsClassifier(n_neighbors=10, metric=self.dist)
        self.knn_model.fit(self.feature_matrix, self.function_list)

    def get_neighbors(self, given_function):
        function_vector = [given_function[x] for x in self.feature_list]
        function_vector_np = np.array(function_vector)
        function_vector_np_reshaped = function_vector_np.reshape(1, len(self.feature_list))
        return [self.function_list[x] for x in self.knn_model.kneighbors(function_vector_np_reshaped)[1][0]]


# Given the library folder name it creates a database of libraries present in it for future queries
# Creating new object : numeric_filter = Numeric_Filter(library_folder_name)
# Requirements : this folder should be in the run directory and the structure of folder should be following:
# library_folder --- library_1_folder ------ library_1_file_1.deb
#      |                    `--------------- library_1_file_2.deb
#      |                     `-------------- many other deb files of this library
#      `-------------library_2_folder ------ ...
#       `------------ ...
# Querying : numeric_filter.query(Query_input)
# Query Input : it takes a dictionary of features of the function in the following format
# {
#     "feature1" : value1,
#     "feature2" : value2,
#     ...
# }
# Query Output : it returns a list of neighbor functions in the following format
# [
#   {
#       "library" : library_of_the_function,
#       "file_name" : which deb file in the library, this function belongs to, 
#       "elf_file" : which elf file in the deb file, this funciton belongs to,
#       "function" : address of the function in the elf file
#   },
#   {
#       ...    
#   },
#   ...
# ]
class Numeric_Filter:
    def __init__(self, library_folder_name):
        # At first time it will create knn model and save it 
        preprocessed_data_file = library_folder_name + "_preprocessed.pickle"
        if os.path.isfile(preprocessed_data_file):
            self.knn_model = pickle.load(open(preprocessed_data_file, 'rb'))
        else:
            function_to_features = dict()
            for library_name in os.listdir(library_folder_name):
                library_path = os.path.join(library_folder_name, library_name)
                for file_name in os.listdir(library_path): 
                    elf_file_paths = get_elf_files_list(os.path.join(library_path, file_name))
                    for elf_file in elf_file_paths:
                        r2_pipe = r2pipe.open(elf_file, flags=['-2'])
                        _ = r2_pipe.cmd("aab")
                        function_list = r2_pipe.cmd("afl ~[0]").split()
                        for function in function_list:
                            function_name = library_name + "_x_" + file_name + "_x_" + elf_file + "_x_" + function
                            function_to_features[function_name] = get_function_features(function, r2_pipe)
                        r2_pipe.quit()
            self.knn_model = KNN_Model(function_to_features)
            pickle.dump(self.knn_model, open(preprocessed_data_file, 'wb'))

    def query(self, given_function):
        knn_query = self.knn_model.get_neighbors(given_function)
        neighbor_list = []
        for neighbor in knn_query:
            library, filename, elf_file, function = neighbor.split("_x_")
            neighbor_list.append({
                "library" : library,
                "file_name" : filename, 
                "elf_file" : elf_file,
                "function" : function
            })
        return neighbor_list


# Test Code
if __name__ == "__main__":
    # Create train and test dataset by taking 2/3 and 1/3 binary files from each libraries
    train_folder = sys.argv[1]
    test_folder = sys.argv[2]
    # Extract functions of train dataset and feed them to kNN : It should be such that they will give us library given the numerical features of a function
    numeric_filter = Numeric_Filter(train_folder)
    # Use test dataset to guess library for the binaries based on matching function
    library_folder_name = test_folder
    feature_list = ['nbbs', 'outdegree', 'nlocals', 'edges', 'nargs', 'T', 'A', 'L', 'All']
    for library_name in os.listdir(library_folder_name):
        library_path = os.path.join(library_folder_name, library_name)
        for file_name in os.listdir(library_path): 
            lib_counter = Counter()
            elf_file_paths = get_elf_files_list(os.path.join(library_path, file_name))
            for elf_file in elf_file_paths:
                r2_pipe = r2pipe.open(elf_file, flags=['-2'])
                _ = r2_pipe.cmd("aab")
                function_list = r2_pipe.cmd("afl ~[0]").split()
                for function in function_list:
                    function_name = library_name + "_x_" + file_name + "_x_" + elf_file + "_x_" + function
                    function_features = get_function_features(function, r2_pipe)
                    neighbor_list = numeric_filter.query(function_features)
                    for x in neighbor_list:
                        lib_counter[x['library']] += 1
                r2_pipe.quit()
            print(library_name, file_name, lib_counter)
    # library_folder_name = sys.argv[1]
    # numeric_filter = Numeric_Filter(library_folder_name)
    # r2_pipe = r2pipe.open("tmp/usr/bin/prezip-bin", flags=["-2"])
    # _ = r2_pipe.cmd("aab")
    # print(numeric_filter.query(get_function_features("0x000010e0", r2_pipe)))
    # r2_pipe.quit()


