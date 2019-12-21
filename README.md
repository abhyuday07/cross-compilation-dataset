# cross-compilation-dataset
This repository will house datasets for cross compilation function variants. 
## Usage
  1. Unzip the dataset file to json format.
  2. The format can be realized by trying the following snippet in python.
```
>>> import json
>>> a = json.load(open("dataset_cross.json",'r'))
>>> print(a.keys())
dict_keys(['lib_name', 'file_path', 'function_name', 'arch', 'optimization_level', 'num_features', 'struct_features'])
```
They can be visualized to be the 7 rows. Each key is mapped to an array.

|   Keys, Index| 0   |  ... |   
|---|---|---|
| 'lib_name'  | fontforge    |   |   
| 'file_path' | lib_src/fontforge/fontforge/threaddummy.c | | 
| 'function_name'  | pthread_create   |   |   
|  'arch' |  dockcross-linux-mips |   |   
| 'optimization_level' | 0 | | 
| 'num_features' | [1, 0, 0, 0, 0, 7, 3, 0, 12] | | 
| 'struct_features' |[1, 0, [134217792], [], [[3, 0,..., 0, 0]], [['A', 'T',..., 'T', 'A']]] | | 

To access attributes of i<sup>th</sup> function, query the following:
```
>>> print(a['function_name'][i])
```
### What are numeric and structural features?
To compare functions from cross platform binary files, they must be brought to a common ground. One such common ground is called intermediate representation.
