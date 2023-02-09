python bnfmarc\pers.py cataviz_new.db
python bnfmarc\doc.py cataviz_new.db
sqlite3 cataviz_new.db < bnfmarc\update.sql
