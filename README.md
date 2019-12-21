# Cross-Compilation-Dataset
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
<p>
To compare functions from cross platform binary files, they must be brought to a common ground. One such common ground is called intermediate representation a.k.a. IR. An intermediate representation is a representation of a program “between” the source and target languages. 
</p>
<p>
While the typical compilation takes source to intermediate representation and then to target representation (popular examples are LLVM), the usage in Reverse Engineering is slightly different. In reverse engineering, the IR is used for a comparison of files subjected to different compilation paths.
</p>
<p>
We have classified all instructions into a handfful of types, mainly 'A' (Arithmetic Instructions), 'L' (Logical Instructions), 'T' (Transfer Instructions), etc. The numerical feature is an array of 7 integers which denote certain features of a function such as number of basic blocks, number of each type of instructions, number of function arguments etc. which can be easily extracted from any Reverse Engineering Platform (like IDA Pro (licensed), radare2 (open-source), and Ghidra (recently open-sourced)). Radare2 was used to generate this dataset. 
</p>
<p>
  Structural features are slightly more elaborate. It is an array of 5 values, the first is the number of basic blocks, the second is the number of edges, the third is the list of ids corresponding to each basic blocks, the fourth is the list of edges between the basic blocks and the last is the array of attributes. Each attribute is an array of instructions in IR corresponding to each basic block. The id is actually the offset of function in the object (.o) file.
</p>

### How is this dataset generated?

<p>
  Dockcross is an open-source platform which can be used to perform cross-compilation. It supports a range of architectures including x86, x64, MIPS, arm etc. Popular open-source libraries like openssl, fontforge etc are used for generating functions.
</p>

### Special credits
Shivam Kumar
