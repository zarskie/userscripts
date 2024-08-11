import os
import hashlib
import argparse

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

def find_duplicates(directory, hash_algorithm='md5'):
    duplicates = {}  # Dictionary to store duplicate file paths
    file_hashes = {}  # Dictionary to store unique file hashes and their paths
    
    # Traverse the directory recursively
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
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

def get_parent_folder_and_file(file_path):
    parent_folder = os.path.basename(os.path.dirname(file_path))
    file_name = os.path.basename(file_path)
    return os.path.join(parent_folder, file_name)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Find duplicate files in a directory.")
    parser.add_argument('directory', type=str, help="The directory to search for duplicate files.")
    args = parser.parse_args()

    # Use the provided directory
    directory = args.directory
    duplicates = find_duplicates(directory)
    
    # Print out the duplicates
    for file_hash, file_list in duplicates.items():
        print(f"Duplicate files for hash {file_hash}:")
        for file_path in file_list:
            print(f"  {get_parent_folder_and_file(file_path)}")

if __name__ == "__main__":
    main()