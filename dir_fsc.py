import os, sys, utils, argparse, json


if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Function Specific Compilation')
    parser.add_argument('source_folder', type=str, help='Path of the source folder')
    args = parser.parse_args()
    codebase_folder_path = args.source_folder
    
    # Get all folders (with their parent folders) which contains their header files
    headers_folder_list = utils.find_all_headers_folders(codebase_folder_path)

    # Log file
    log_dict = dict()
    log_dict['success'] = list()
    log_dict['fail'] = list()
    # Walk in the codebase to find source files
    compile_sucess = 0
    total_source_files_num = 0
    for root, _, files in os.walk(codebase_folder_path):
        for _file in files:
            if _file.endswith('.c') or _file.endswith('.cpp'):
                file_path = os.path.join(root, _file)
                compile_exit_value = utils.compile_to_object_file(file_path, headers_folder_list)
                if compile_exit_value == 0:
                    compile_sucess += 1
                    log_dict['success'].append(file_path)
                else:
                    log_dict['fail'].append(file_path)
                total_source_files_num += 1

    # Save log file
    json.dump(log_dict, open('log_file.json', 'w'), indent=4)

    # Print the results
    print("Number of files sucessfully compiled is %d." % compile_sucess)
    print("Total number of source files is %d." % total_source_files_num)
