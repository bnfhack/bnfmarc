
UPDATE contrib SET type = NULL;
-- writes
UPDATE contrib SET type = 1 WHERE role IN (62, 70, 90, 330);
-- edits
UPDATE contrib SET type = 2 WHERE role IN (3, 72, 75, 80, 100, 205, 212, 220, 270, 340, 651, 710, 727, 735);
-- translates
UPDATE contrib SET type = 3 WHERE role IN (730);
-- illustrates
UPDATE contrib SET type = 4 WHERE role IN (40, 440, 520, 521, 522, 523, 524, 530, 531, 532, 533, 534, 705, 760);
-- music
UPDATE contrib SET type = 5 WHERE role IN (230, 233, 236, 250, 510, 721);
-- set year of contributions
UPDATE contrib SET year = (SELECT year FROM doc WHERE contrib.doc = doc.id);


UPDATE pers SET 
    -- docs count as an author
    docs=(SELECT count(*) FROM contrib WHERE pers=pers.id AND type = 1),
    -- first doc published as author
    doc1=(SELECT year FROM contrib WHERE pers=pers.id AND type = 1 ORDER BY year LIMIT 1)
;

VACUUM;