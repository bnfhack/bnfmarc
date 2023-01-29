#!/bin/bash
DATA=$(realpath $(dirname $0)/../data)/ # $(`basename $0`)
echo download in $DATA

# geographical records P2819_*
wget -nd -r -P $DATA ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/Geo/Geo_2021/Geo_2021_Unimarc_UTF8
# authority record P1486_*
wget -nd -r -P $DATA ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/Pcts/Pcts_2021/Pcts_2021_Unimarc_UTF8/*.UTF8
# bibliographical records …—1969 P1187_*
wget -nd -r -P $DATA ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/CGI/CGI_2021/CGI_2021_Unimarc_UTF8/*.UTF8
# bibliographical records 1970–… P174_*
wget -nd -r -P $DATA ftp://PRODUIT_RETRO:b9rZ2As7@pef.bnf.fr/PRODUIT_RETRO/BNF-Livres/BNF-Livres_2021/BNF-Livres_2021_Unimarc_UTF8/*.UTF8
