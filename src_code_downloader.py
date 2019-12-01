
# Start Download

import os
import subprocess
import sys
import csv
import multiprocessing


def clone_lib(lib, lib_to_link, lib_to_tag):
    print("Cloning of library %s is started." % lib)
    current_path = os.getcwd()
    try:
        # Create folder for library
        lib_folder = "lib_src"
        lib_path = os.path.join(lib_folder, lib)
        if os.path.isdir(lib_path):
            print("Seems like lib %s is already cloned." % lib)
        else:
            os.makedirs(lib_path)
            # Clone library
            subprocess.check_output("git clone %s %s"%(lib_to_link[lib],lib_path), shell = True)
            # Checkout the version of the library
            current_path = os.getcwd()
            os.chdir(lib_path)
            _ = os.system("git checkout %s" % lib_to_tag[lib])
            os.chdir(current_path)
            # Output the success message
            print("Library %s is sucessfully cloned at %s and the version corresponding to tag %s is checked out." % (lib, lib_path, lib_to_tag[lib]))
    except Exception as e:
        os.chdir(current_path)
        print("Download failed for %s"%(lib))
        print(e)


if __name__ == "__main__":
    csv_file = open(sys.argv[1])
    # Get URL in proper shape in the form of dictionary
    lib_to_link = dict()
    lib_to_tag = dict()
    csv_reader = csv.reader(csv_file, delimiter = ',')
    for row in csv_reader:
        if row[0] not in lib_to_link:
            if row[1][0:9] == "https://:":
                row[1] = "https://"+row[1][9:]
            if row[1][0:15] == "git@github.com:":
                row[1] = "https://github.com/" + row[1][15:-4]
            if row[1].startswith('git://'):
                row[1] = "https://" + row[1][6:-4]
            lib_to_link[row[0]] = row[1]
            lib_to_tag[row[0]] = row[2]
    pool = multiprocessing.Pool(processes = 10)
    results_of_processes = [pool.apply_async(clone_lib, args=(lib,lib_to_link,lib_to_tag, ), callback = None ) for lib in lib_to_link]
    # for lib in lib_to_link:
    pool.close()
    pool.join()
