import argparse
import json
import os
import utils


# Main function
if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Dataset Generator')
    parser.add_argument('library_folder_path', type=str, help='Path of the folder containing source code of all libraries')
    args = parser.parse_args()
    library_folder_path = args.library_folder_path

    # Result dict
    result_dict = dict()
    result_dict['file_path'] = []
    result_dict['function_name'] = []
    result_dict['optimization_level'] = []
    result_dict['nbbs'] = []
    result_dict['outdegree'] = []
    result_dict['nlocals'] = []
    result_dict['edges'] = []
    result_dict['nargs'] = []
    result_dict['T'] = []
    result_dict['A'] = []
    result_dict['L'] = []
    result_dict['All'] = []

    # Look through each of the library
    for lib_name in os.listdir(library_folder_path):
        lib_path = os.path.join(library_folder_path, lib_name)
        codebase_folder_path = lib_path
        # Get all folders (with their parent folders) which contains their header files
        headers_folder_list = utils.find_all_headers_folders(codebase_folder_path)
        # Walk in the codebase to find source files
        compile_sucess = 0
        total_source_files_num = 0
        for root, _, files in os.walk(codebase_folder_path):
            for _file in files:
                if _file.endswith('.c') or _file.endswith('.cpp'):
                    # Check if file can be compiled
                    compiled_sucessfully = False
                    file_path = os.path.join(root, _file)
                    compile_exit_value = utils.compile_to_object_file(file_path, headers_folder_list)
                    if compile_exit_value == 0:
                        compile_sucess += 1
                        compiled_sucessfully = True
                    total_source_files_num += 1
                    # Extract Numerical features
                    if compiled_sucessfully:
                        for optimization_level in range(4):
                            # Compile for this optimization level
                            compile_exit_value = utils.compile_to_object_file(file_path, headers_folder_list, extra_flags="-O" + str(optimization_level))
                            assert compile_exit_value == 0
                            # Retrieve function list from source code
                            func_list_from_src = utils.get_func_list(file_path)
                            # Retrieve features
                            func_features = utils.get_func_nf_sf_one_file("object_file", func_list_from_src)
                            for func_name in func_features:
                                # print(func_features[func_name]["features"][0][0])
                                result_dict['file_path'].append(file_path)
                                result_dict['function_name'].append(func_name)
                                result_dict['optimization_level'].append(optimization_level)
                                result_dict['nbbs'].append(func_features[func_name]["features"][0][0])
                                result_dict['outdegree'].append(func_features[func_name]["features"][0][1])
                                result_dict['nlocals'].append(func_features[func_name]["features"][0][2])
                                result_dict['edges'].append(func_features[func_name]["features"][0][3])
                                result_dict['nargs'].append(func_features[func_name]["features"][0][4])
                                result_dict['T'].append(func_features[func_name]["features"][0][5])
                                result_dict['A'].append(func_features[func_name]["features"][0][6])
                                result_dict['L'].append(func_features[func_name]["features"][0][7])
                                result_dict['All'].append(func_features[func_name]["features"][0][8])

        # Print Number of files compiled
        print("Library name: %s, Total source files: %d, Compiled source files: %d" % (lib_name, total_source_files_num, compile_sucess))

    # Save dictionary
    json.dump(result_dict, open('dataset1.json', 'w'),  indent=4)
