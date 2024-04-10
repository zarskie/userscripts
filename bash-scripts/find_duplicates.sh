#!/usr/bin/env bash
# set -euxo pipefail
source_dirs=()
target_dirs=()
remove_duplicates=false

find_duplicate_files() {
	declare -a files
	declare -a full_paths
	output=""
	for dir in "${source_dirs[@]}"; do
		while read -r line; do
			files+=("$line")
		done < <(find "$dir" -type f -exec basename {} \;)
	done
	mapfile -t duplicates < <(printf "%s\n" "${files[@]}" | sort | uniq -d)
	if [ ${#duplicates[@]} -eq 0 ]; then
		echo "No duplicates found, exiting..."
		exit
	fi
	output=$(for file in "${duplicates[@]}"; do
		for dir in "${source_dirs[@]}"; do
			while read -r path; do
				parent_dir=$(basename "$(dirname "$path")")
				echo "$parent_dir/$file"
			done < <(find "$dir" -type f -name "$file")
		done
	done)
	output=$(echo -e "Directories\tDuplicates\n$output" | awk -F'/' 'NR > 1 && $2 != prev { print "" } { print; prev = $2 }' | sed 's/\//\t/' | sed 's/^[[:space:]]*$/_/' | column -t -s $'\t' | sed 's/_//')
	echo "$output"
	for file in "${duplicates[@]}"; do
		for dir in "${source_dirs[@]}"; do
			while read -r path; do
				full_paths+=("$path")
			done < <(find "$dir" -type f -name "$file")
		done
	done
	if [[ "$remove_duplicates" == true ]]; then
		echo
		for full_path in "${full_paths[@]}"; do
			extracted_path=$(dirname "$full_path")
			for path in "${target_dirs[@]}"; do
				if [[ "$extracted_path" == "$path" ]]; then
					rm "$full_path"
					echo "Removed duplicate: $full_path"
				fi
			done
		done
	fi
}

handle_options() {
	while getopts ":s:t:rh" opt; do
		case $opt in
		s)
			source_dirs+=("$OPTARG")
			;;
		t)
			target_dirs+=("$OPTARG")
			;;
		r)
			remove_duplicates=true
			;;
		h)
			display_help
			;;
		\?)
			echo "Invalid option: -$OPTARG"
			display_help
			;;
		:)
			echo "Invalid option: -$OPTARG requires an argument"
			display_help
			;;
		esac
	done
}

check_config() {
	for dir in "${source_dirs[@]}"; do
		if [ ! -d "$dir" ]; then
			echo "ERROR: Your source directory ($dir) does not exist please check your configuration"
			exit 1
		fi
	done
	if [[ "$remove_duplicates" == true ]]; then
		if [ ${#target_dirs[@]} -eq 0 ]; then
			echo "ERROR: You must set a target directory (-t) to remove duplicates from"
			exit 1
		fi
		for dir in "${target_dirs[@]}"; do
			if [ ! -d "$dir" ]; then
				echo "ERROR: Your target directory ($dir) does not exist please check your configuration"
				exit 1
			fi
		done
	else
		if [ ${#target_dirs[@]} -gt 0 ]; then
			echo "ERROR: Target directory (-t) should only be set if removing duplicates (-r)"
			exit 1
		fi
	fi
}

display_help() {
	echo "This script will compare defined directorie(s) recursivley to a defined target directorie(s), and either remove or list all duplicate file names."
	echo "Options:"
	echo " -s    : Set the source directorie(s) - example -s /foo -s /bar"
	echo " -t    : Set the target directorie(s) - example -t /foo -t /bar"
	echo " -r    : Remove duplicates in target directorie(s) (default: False)"
	echo " -h    : Show this help message"
	exit 0
}

handle_options "$@"
check_config
find_duplicate_files
