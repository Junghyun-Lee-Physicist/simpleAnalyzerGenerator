# CMS Analysis Framework Generator

This tool (`setup_framework.py`) is a wrapper that automates the initialization of a ROOT-based analysis framework. It replaces the manual process of running `MakeClass`, writing a `main` function, and creating a `Makefile`.

## Prerequisites

* **Python 3**
* **ROOT** (Must be sourced, e.g., `source /cvmfs/sft.cern.ch/lcg/views/LCG_.../setup.sh` or standard CMS environment)
* A sample ROOT file (NanoAOD or MiniAOD) to extract the Tree structure.

## Usage

### 1. Generate the Code
Run the python script. You must provide a sample file.

```bash
# Basic Usage (Default class name: CMSAnalyzer, Tree: Events)
python3 setup_framework.py -f /path/to/sample_file.root

# Custom Usage
python3 setup_framework.py -f sample.root -t Events -c MyPhysicsAnalyzer
```

**Output:** The script will generate the following files in your current directory:

- `CMSAnalyzer.h`: Header file defining the Tree structure.
    
- `CMSAnalyzer.C`: Source file containing the `Loop()` function (Where you write your cuts/histograms).
    
- `main.cc`: C++ runner that handles file lists and TChains.
    
- `Makefile`: Configuration to compile everything.
    

### 2. Compile

Simply run `make`.

Bash

```
make
```

This will produce an executable named **`runAnalysis`**.

### 3. Run

Prepare a text file containing the list of ROOT files you want to analyze (e.g., `file_list.txt`).

Bash

```
./runAnalysis file_list.txt
```

---

## Workflow Example

1. **Get File List:** Use your DAS script to get files.
    
    ```Bash
    python3 get_file_list.py > file_list.txt
    ```
    
2. **Setup Framework:** (Only needed once)
    
    ```Bash
    # Use one of the files from the list as a template
    python3 setup_framework.py -f root://cms-xrd-global.cern.ch//store/mc/.../tree_1.root
    ```
    
3. **Edit Code:** Open `CMSAnalyzer.C` and modify the `Loop()` function to add your physics logic.
    
4. **Build & Run:**
    
    ```Bash
    make
    ./runAnalysis file_list.txt
    ```
    
---

## Key Features of this Wrapper

1.  **Automated `MakeClass`**: It performs the exact same operation as opening ROOT and typing `tree->MakeClass()`, but does it silently in the background.
2.  **Integrated `main.cc`**: You don't need to write the C++ boilerplate code to read `std::ifstream` or setup `TChain`. It creates a robust `main.cc` that links to your Analyzer.
3.  **Smart Makefile**: It creates a `Makefile` that handles the linking between the `.cc` (main) and `.C` (Analyzer) files automatically using `root-config`.
4.  **Flexibility**: You can change the class name (`-c`) or the tree name (`-t`) via arguments without changing the python code.
