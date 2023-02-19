
-- type of contribution
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


-- probably error in date
UPDATE doc SET year = NULL WHERE year < 1450;
-- set year of contributions
UPDATE contrib SET year = (SELECT year FROM doc WHERE contrib.doc = doc.id);
-- set birthyear of contributions (for checks)
UPDATE contrib SET birthyear = (SELECT birthyear FROM auth WHERE contrib.auth = auth.id);
-- delete date before birth of author
UPDATE contrib SET year = NULL WHERE birthyear IS NOT NULL AND year < birthyear;

-- set year of a study about some one
UPDATE about SET year = (SELECT year FROM doc WHERE about.doc = doc.id);

-- maybe a bug
UPDATE doc SET place = NULL WHERE place = '';

UPDATE auth SET 
    -- docs count as an author
    docs = (SELECT count(*) FROM contrib WHERE auth=auth.id AND type = 1),
    -- first doc published as author (be careful of NULL year)
    doc1 = (SELECT year FROM contrib WHERE auth=auth.id AND type = 1 ORDER BY year ASC NULLS LAST LIMIT 1),
    -- ensure a date to select authors by date
    generation = birthyear
;
-- ensure a date to select authors by date
UPDATE auth SET generation = deathyear - 50 WHERE generation IS NULL AND deathyear IS NOT NULL;
UPDATE auth SET generation = doc1 WHERE generation IS NULL AND doc1 IS NOT NULL;

UPDATE doc SET 
    type1=(SELECT type FROM auth WHERE auth1=auth.id ),
    gender1=(SELECT gender FROM auth WHERE auth1=auth.id )
;


VACUUM;
PRAGMA optimize;
