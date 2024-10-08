#!/usr/bin/env bash
proj="$(realpath "$(dirname "$0")")"
bib="$(realpath $proj/../bib/)"

i=-1
while IFS=, read -r dir url glob
do
  # passer les lignes vides
  [[ $dir == "" ]] && continue
  # passer les commentaires
  [[ ${dir:0:1} == "#" ]] && continue
  i=$((i + 1))
  # passer la première ligne
  [ $i -eq 0 ] && continue
  echo " -- $i   $dir   $url   $glob"
  if [ ! -d "$proj/$dir" ]; then
    mkdir -p $proj/$dir
    git clone $url $proj/$dir
  else
    pushd $proj/$dir >/dev/null
    git pull
    popd >/dev/null
  fi
done < $proj/../obvilgit.csv
