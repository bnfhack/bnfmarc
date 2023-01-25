
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


UPDATE person SET 
  -- premier document publié du vivant de l’auteur
  doc1=(SELECT date FROM contrib WHERE pers=pers.id AND type = 1 ORDER BY date LIMIT 1)
)