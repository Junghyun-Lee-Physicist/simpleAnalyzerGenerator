#!/usr/bin/env python3
import sys
import os
import argparse

def main():
    """
    CMS Analysis Framework Generator
    
    1. Opens the sample ROOT file.
    2. Creates a directory named after the Class.
    3. Moves into that directory.
    4. Generates:
       - Analyzer skeleton (MakeClass)
       - main.cc (Execution driver)
       - Makefile (Compilation)
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
    print(f"[INFO] Initializing Framework Generation")
    print(f"[INFO] Target Directory: ./{output_dir}")
    print(f"[INFO] Sample File     : {sample_file}")
    print("-" * 60)

    # --- 2. Check ROOT Availability ---
    try:
        import ROOT
    except ImportError:
        print("[ERROR] Could not import ROOT module. Please check your environment.")
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

    # --- 4. Create Directory & Move ---
    if os.path.exists(output_dir):
        print(f"[WARNING] Directory '{output_dir}' already exists.")
    else:
        try:
            os.makedirs(output_dir)
            print(f"[INFO] Created directory: {output_dir}")
        except OSError as e:
            print(f"[ERROR] Failed to create directory {output_dir}: {e}")
            sys.exit(1)

    original_cwd = os.getcwd()
    os.chdir(output_dir)
    print(f"[INFO] Changed working directory to: {os.getcwd()}")

    # --- 5. Run MakeClass ---
    print(f"[INFO] Running MakeClass('{class_name}')...")
    tree.MakeClass(class_name)
    f.Close() 

    if not (os.path.exists(f"{class_name}.C") and os.path.exists(f"{class_name}.h")):
        print("[ERROR] MakeClass failed to generate files.")
        sys.exit(1)


    # --- 6. Generate main.cc ---
    main_filename = "main.cc"
    print(f"[INFO] Generating C++ entry point: {main_filename}...")
    
    main_code = f"""/**
 * @file {main_filename}
 * @brief Main driver for {class_name}.
 */

#include "{class_name}.h"
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
    makefile_name = "Makefile"
    print(f"[INFO] Generating Makefile: {makefile_name}...")

    makefile_code = f"""# Auto-generated Makefile for {class_name}

CXX = g++
CXXFLAGS = -O2 -Wall -fPIC $(shell root-config --cflags)
LDFLAGS = $(shell root-config --libs)

TARGET = runAnalysis

SRCS = {main_filename} {class_name}.C
OBJS = $(SRCS:.cc=.o)
OBJS := $(OBJS:.C=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) -o $@ $^ $(LDFLAGS)
	@echo "-----------------------------------------"
	@echo " Build Complete! Executable: ./$(TARGET)"
	@echo "-----------------------------------------"

%.o: %.cc
	$(CXX) $(CXXFLAGS) -c $< -o $@

%.o: %.C
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f *.o $(TARGET)
"""
    with open(makefile_name, "w") as f_make:
        f_make.write(makefile_code)

    # --- 8. Finalize ---
    os.chdir(original_cwd)

    print("-" * 60)
    print(f"[DONE] Framework generated in directory: {output_dir}/")
    print(f"[DONE] Please check README.md in the repository for coding examples.")
    print("-" * 60)

if __name__ == "__main__":
    main()
