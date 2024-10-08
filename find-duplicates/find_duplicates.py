import os
import hashlib
import argparse
from tqdm import tqdm # type: ignore
from tabulate import tabulate # type: ignore

def compute_hash(file_path, algorithm='md5', chunk_size=1024):
    # Create a hash object
    hash_func = hashlib.new(algorithm)
    # Open the file in binary mode
    with open(file_path, 'rb') as f:
        # Read the file in chunks to avoid memory issues with large files
        while chunk := f.read(chunk_size):
            # Update the hash object with the chunk
            hash_func.update(chunk)
    # Return the hexadecimal digest of the hash
    return hash_func.hexdigest()

def find_duplicates_in_directories(directories, hash_algorithm='md5'):
    duplicates = {}  # Dictionary to store duplicate file paths
    file_hashes = {}  # Dictionary to store unique file hashes and their paths
    
    # List all files to process and get the total count for the progress bar
    all_files = []
    for directory in directories:
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                all_files.append(os.path.join(dirpath, filename))
    
    # Traverse the directory and compute hashes
    for file_path in tqdm(all_files, desc="Processing files", unit="file"):
        try:
            # Compute the hash of the current file
            file_hash = compute_hash(file_path, algorithm=hash_algorithm)
            
            # Check if this hash already exists in file_hashes
            if file_hash in file_hashes:
                # If the hash is already in file_hashes, it's a duplicate
                if file_hash not in duplicates:
                    # If this hash is not already in duplicates, add the original file
                    duplicates[file_hash] = [file_hashes[file_hash]]
                # Add the current file path to the list of duplicates for this hash
                duplicates[file_hash].append(file_path)
            else:
                # If the hash is not in file_hashes, store it with its file path
                file_hashes[file_hash] = file_path
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    return duplicates

def find_duplicates_between_directories(source_directories, target_directory, hash_algorithm='md5'):
    duplicates = {}  # Dictionary to store duplicate file paths
    file_hash_to_path = {}  # Dictionary to store unique file hashes and their paths
    
    # Collect all files from the source directories and compute their hashes
    source_files = []
    for directory in source_directories:
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                source_files.append(os.path.join(dirpath, filename))
    for file_path in tqdm(source_files, desc="Processing source files", unit="file"):
        try:
            file_hash = compute_hash(file_path, algorithm=hash_algorithm)
            file_hash_to_path[file_hash] = file_path
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    # Collect all files from the target directory
    target_files = []
    for dirpath, _, filenames in os.walk(target_directory):
        for filename in filenames:
            target_files.append(os.path.join(dirpath,filename))
    
    # Check for duplicates in the target directory
    for file_path in tqdm(target_files, desc="Processing target files", unit="file"):
        try:
            file_hash = compute_hash(file_path, algorithm=hash_algorithm)
            if file_hash in file_hash_to_path:
                if file_hash not in duplicates:
                    duplicates[file_hash] = [file_hash_to_path[file_hash]]
                duplicates[file_hash].append(file_path)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    return duplicates

def get_parent_folder_and_file(file_path):
    parent_folder = os.path.basename(os.path.dirname(file_path))
    file_name = os.path.basename(file_path)
    return parent_folder, file_name

def remove_duplicates_in_target(duplicates, target_directory):
    files_to_remove = []
    for file_list in duplicates.values():
        for file_path in file_list:
            if file_path.startswith(target_directory):
                files_to_remove.append(file_path)
    
    for file_path in files_to_remove:
        try:
            os.remove(file_path)
            print(f"Removed duplicate file: {file_path}")
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Find and optionally remove duplicate files in one or more source directories, with an optional target directory.")
    parser.add_argument('-s', '--source', type=str, nargs='+', required=False, help="One or more source directories to search for duplicate files.")
    parser.add_argument('-t', '--target', type=str, nargs='?', default=None, help="The optional target directory to check for duplicates against the source directories.")
    parser.add_argument('-r', '--remove', action='store_true', help="Remove duplicates found in the target directory.")
    args = parser.parse_args()

    if not (args.source or args.target):
        parser.print_help()
        return

    # Use the provided directory
    source_directories = args.source
    target_directory = args.target
    
    if source_directories and target_directory:
        duplicates = find_duplicates_between_directories(source_directories, target_directory)
    elif source_directories:
        duplicates = find_duplicates_in_directories(source_directories)
    else:
        duplicates = {}
    
    # Check if only target directory is provided without any source directories
    if args.target and not args.source:
        print("Error: You must specify at least one source directory with -s or --source when using a target directory.")
        parser.print_help()
        return
    
    # Check if the target directory is within any of the source directories
    if args.target and args.source:
        for source_dir in args.source:
            if os.path.commonpath([source_dir]) == os.path.commonpath([source_dir, args.target]):
                print("Error: Target directory cannot be within a source directory.")
                parser.print_help()
                return

    # Check if any source directory is within the target directory
    if args.target and args.source:
        for source_dir in args.source:
            if os.path.commonpath([args.target]) == os.path.commonpath([args.target, source_dir]):
                print("Error: Source directory cannot be within the target directory.")
                parser.print_help()
                return
                    
    # Print out the duplicates
    if duplicates:
        table_data = []
        for file_hash, file_list in duplicates.items():
            parent_folder, file_name = get_parent_folder_and_file(file_list[0])
            table_data.append([file_hash, parent_folder, file_name])
            for file_path in file_list[1:]:
                parent_folder, file_name = get_parent_folder_and_file(file_path)
                table_data.append(["", parent_folder, file_name])
            table_data.append(["", "", ""])
        print(tabulate(table_data, headers=["Hash", "Directory", "File"], tablefmt="pretty"))
        
        if args.remove:
            if target_directory:
                remove_duplicates_in_target(duplicates, target_directory)
            else:
                print("Error: Target directory must be specified with -t or --target when using -r or --remove.")
    else:
        print("No duplicates found.")

if __name__ == "__main__":
    main()