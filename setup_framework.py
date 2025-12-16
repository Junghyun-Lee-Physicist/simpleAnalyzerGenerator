#!/usr/bin/env python3
import sys
import os
import argparse
import shutil

def main():
    """
    CMS Analysis Framework Generator (Structured Version)
    
    Output Structure:
      TargetDir/
       ├── Makefile
       ├── include/
       │    └── CMSAnalyzer.h
       └── src/
            ├── CMSAnalyzer.C
            └── main.cc
    """

    # --- 1. Argument Parsing ---
    parser = argparse.ArgumentParser(description="Generate a CMS ROOT Analysis Framework via MakeClass")
    parser.add_argument("-f", "--file", required=True, help="Path to a sample ROOT file (Raw string used as-is)")
    parser.add_argument("-t", "--tree", default="Events", help="Name of the TTree in the file (default: Events)")
    parser.add_argument("-c", "--class", dest="classname", default="CMSAnalyzer", help="Name of the Analyzer class")
    
    args = parser.parse_args()
    
    sample_file = args.file
    tree_name = args.tree
    class_name = args.classname
    output_dir = class_name

    print("-" * 60)
    print(f"[INFO] Initializing Structured Framework Generation")
    print(f"[INFO] Target Directory: ./{output_dir}")
    print(f"[INFO] Structure       : src/ (Source), include/ (Header)")
    print(f"[INFO] Sample File     : {sample_file}")
    print("-" * 60)

    # --- 2. Check ROOT Availability ---
    try:
        import ROOT
    except ImportError:
        print("[ERROR] Could not import ROOT module.")
        sys.exit(1)

    # --- 3. Open File & Get Tree ---
    print(f"[INFO] Opening file to extract TTree structure...")
    ROOT.gROOT.SetBatch(True)
    
    f = ROOT.TFile.Open(sample_file, "READ")
    if not f or f.IsZombie():
        print(f"[ERROR] Failed to open file: {sample_file}")
        sys.exit(1)

    tree = f.Get(tree_name)
    if not tree:
        print(f"[ERROR] TTree '{tree_name}' not found.")
        f.Close()
        sys.exit(1)

    print(f"[INFO] Found TTree '{tree_name}' with {tree.GetEntries()} entries.")

    # --- 4. Prepare Directory Structure ---
    # Create the main directory and sub-directories (src, include)
    if os.path.exists(output_dir):
        print(f"[WARNING] Directory '{output_dir}' already exists.")
    else:
        try:
            os.makedirs(output_dir)
            os.makedirs(os.path.join(output_dir, "src"))
            os.makedirs(os.path.join(output_dir, "include"))
            print(f"[INFO] Created directory structure: src/, include/")
        except OSError as e:
            print(f"[ERROR] Failed to create directories: {e}")
            sys.exit(1)

    # Save original path
    original_cwd = os.getcwd()
    
    # Move into the output directory to run MakeClass
    os.chdir(output_dir)
    print(f"[INFO] Changed working directory to: {os.getcwd()}")

    # --- 5. Run MakeClass & Move Files ---
    print(f"[INFO] Running MakeClass('{class_name}')...")
    
    # MakeClass generates files in the CURRENT directory
    tree.MakeClass(class_name)
    f.Close() 

    # Check and Move files
    if os.path.exists(f"{class_name}.C") and os.path.exists(f"{class_name}.h"):
        # Move .C -> src/
        shutil.move(f"{class_name}.C", f"src/{class_name}.C")
        # Move .h -> include/
        shutil.move(f"{class_name}.h", f"include/{class_name}.h")
        print(f"[INFO] Moved {class_name}.C -> src/")
        print(f"[INFO] Moved {class_name}.h -> include/")
    else:
        print("[ERROR] MakeClass failed to generate files.")
        sys.exit(1)


    # --- 6. Generate src/main.cc ---
    # We create main.cc directly inside src/
    main_filename = "src/main.cc"
    print(f"[INFO] Generating C++ entry point: {main_filename}...")
    
    main_code = f"""/**
 * @file main.cc
 * @brief Main driver for {class_name}.
 */

#include "{class_name}.h" // Makefile will handle the include path
#include <iostream>
#include <fstream>
#include <string>
#include "TChain.h"
#include "TString.h"

int main(int argc, char* argv[]) {{
    if (argc < 2) {{
        std::cout << "Usage: " << argv[0] << " <file_list.txt>" << std::endl;
        return 1;
    }}

    std::string listFileName = argv[1];
    std::cout << "[Main] Processing file list: " << listFileName << std::endl;

    TChain *chain = new TChain("{tree_name}");
    std::ifstream infile(listFileName);
    std::string line;
    int nFiles = 0;

    if (infile.is_open()) {{
        while (std::getline(infile, line)) {{
            if (line.empty() || line[0] == '#') continue;
            chain->Add(line.c_str());
            nFiles++;
        }}
        infile.close();
    }} else {{
        std::cout << "[Error] Cannot open file list!" << std::endl;
        return 1;
    }}

    if (nFiles == 0) {{
        std::cout << "[Warning] No files added to chain." << std::endl;
    }}

    std::cout << "[Main] Total " << nFiles << " files added to TChain." << std::endl;

    {class_name} t(chain);
    
    std::cout << "[Main] Starting Event Loop..." << std::endl;
    t.Loop();
    std::cout << "[Main] Analysis Finished." << std::endl;

    return 0;
}}
"""
    with open(main_filename, "w") as f_main:
        f_main.write(main_code)


    # --- 7. Generate Makefile ---
    # The Makefile must now look into src/ for source files 
    # and include/ for header files (-Iinclude)
    makefile_name = "Makefile"
    print(f"[INFO] Generating Makefile: {makefile_name}...")

    makefile_code = f"""# Auto-generated Makefile for {class_name}

CXX = g++
# [Important] Add -Iinclude so the compiler can find the header file
INC = -Iinclude
CXXFLAGS = -O2 -Wall -fPIC $(shell root-config --cflags) $(INC)
LDFLAGS = $(shell root-config --libs)

TARGET = runAnalysis

# Source files are now in src/
SRCS = src/main.cc src/{class_name}.C
OBJS = $(SRCS:.cc=.o)
OBJS := $(OBJS:.C=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) -o $@ $^ $(LDFLAGS)
	@echo "-----------------------------------------"
	@echo " Build Complete! Executable: ./$(TARGET)"
	@echo "-----------------------------------------"

# Rule for .cc files in src/
src/%.o: src/%.cc
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Rule for .C files in src/
src/%.o: src/%.C
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f src/*.o $(TARGET)
"""
    with open(makefile_name, "w") as f_make:
        f_make.write(makefile_code)

    # --- 8. Finalize ---
    os.chdir(original_cwd)

    print("-" * 60)
    print(f"[DONE] Framework generated in directory: {output_dir}/")
    print(f"[NOTE] Source files are in '{output_dir}/src/'")
    print(f"[NOTE] Header files are in '{output_dir}/include/'")
    print("-" * 60)

if __name__ == "__main__":
    main()
