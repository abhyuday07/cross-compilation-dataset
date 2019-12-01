import os, sys, utils, argparse


if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description='Function Specific Compilation')
    parser.add_argument('input_source_file', type=str, help='Path of the input source file')
    parser.add_argument('source_folder', type=str, help='Path of the source folder')
    args = parser.parse_args()
    cpp_file_path = args.input_source_file
    codebase_folder_path = args.source_folder
    
    # Get all folders (with their parent folders) which contains their header files
    headers_folder_list = utils.find_all_headers_folders(codebase_folder_path)

    # Compile to get object file
    utils.compile_to_object_file(cpp_file_path, headers_folder_list)

    # Retrieve function list from source code
    func_list_from_src = utils.get_func_list(cpp_file_path)

    # Save decompiled function
    utils.save_decompiled_functions("object_file", func_list_from_src)
