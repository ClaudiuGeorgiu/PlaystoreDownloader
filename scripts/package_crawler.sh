#!/usr/bin/env bash

# The directory containing this script.
DIR=$(dirname "$(readlink -f "${0}")")

# Set the working directory to the directory where this script is run.
cd -P -- "${DIR}" || exit

declare -A found_packages
declare -A not_explored_packages

# Initial list with package names to explore.
not_explored_packages["com.whatsapp"]=1
not_explored_packages["com.facebook.katana"]=1
not_explored_packages["com.spotify.music"]=1

# This function takes a package name string as input, visits the corresponding Google
# Play Store page and crawls all the other package names in that page.
get_more_packages() {
  # Make sure to have lynx installed.
  output="$(lynx --dump -nonumbers \
  "https://play.google.com/store/apps/details?id=$1" \
  | grep -oP "(?<=://play.google.com/store/apps/details\?id=)[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+" \
  | sort | uniq)"

  # Return all the package names found when visiting the Google Play Store page
  # of the input package.
  echo "${output}"
}

# While there are package names to explore...
while [[ "${#not_explored_packages[@]}" -ne 0 ]]; do
  # For each package name p1 not yet explored...
  for p1 in "${!not_explored_packages[@]}"; do
    # For each package name p2 found in p1's details page in the Google Play Store...
    while read -r p2; do
      if [[ -n "${p2// }" ]] && ! [[ ${found_packages["${p2}"]+_} ]]; then
        # Package name p2 was not explored yet.
        not_explored_packages["${p2}"]=1;
        found_packages["${p2}"]=1;
        echo "${p2}"
        echo "${p2}" >>"${DIR}/packages.txt"
      fi
    done <<< "$(get_more_packages "${p1}")"
    # This package name is now explored, now it can be removed from the list.
    unset not_explored_packages["${p1}"]
  done
done

echo "+++ Crawling completed! +++"
