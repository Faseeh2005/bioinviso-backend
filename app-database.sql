--for location but not implemented right now
select version();


create table users(
	user_id serial primary key,
	username varchar(100) unique not null,
	role varchar(100)
);

INSERT INTO users (username, expertise_level, role,email,password) 
VALUES ('jazib', 'begin', 'researcher','jazib@gmail.com','1234');

ALTER TABLE users DROP COLUMN expertise_level;

select * from users;

alter table users add column email varchar(100);
ALTER TABLE users ADD COLUMN password VARCHAR(255) NOT NULL;

-- create table species(
-- 	species_id serial primary key not null,
-- 	genus_name varchar(100) not null,
-- 	species_name varchar(100) not null
-- );

SELECT setval('species_species_id_seq', (SELECT MAX(species_id) FROM species));
select * from species;

create table species(
	species_id serial primary key,
	species_name varchar(100) not null
);

select * from observation;
ALTER TABLE observation ADD COLUMN Topic VARCHAR(50);
ALTER TABLE observation ADD COLUMN Headline VARCHAR(255);

create table observation(
	observation_id serial primary key,
	user_id int references users(user_id),
	species_id int references species(species_id),
	research_content text,
	latitude double precision,
	longitude double precision,
	observed_at timestamp with time zone default now(),
	is_native boolean
);

create table forum(
	post_id serial primary key,
	obs_id int references observation(observation_id),
	user_id int references users(user_id),
	comments text,
	parent_id int references forum(post_id)
);

create table regions(
	region_id serial primary key,
	region_name varchar(100),
	boundary jsonb
);

create table habitats(
	region_id int references regions(region_id),
	species_id int references species(species_id),
	primary key (region_id, species_id) --unique pairings
);

INSERT INTO users (username, expertise_level, role)
VALUES 
('ali', 'beginner', 'user'),
('faseeh', 'intermediate', 'admin');

-- INSERT INTO species (genus_name, species_name)
-- VALUES 
-- ('Passer', 'domesticus'),
-- ('Corvus', 'splendens'),
-- ('Canis', 'lupus');

INSERT INTO species(species_id, species_name)
VALUES 
(1, 'House Sparrow'),
(2, 'Crow'),
(3, 'Wolf');

INSERT INTO regions (region_name, boundary)
VALUES 
(
  'Topi',
  '[[34.07,72.48],[34.08,72.50],[34.06,72.52]]'
),
(
  'Swabi',
  '[[34.12,72.45],[34.14,72.47],[34.10,72.49]]'
);

INSERT INTO habitats (region_id, species_id)
VALUES 
(1, 1),
(1, 2),
(2, 3);

INSERT INTO observation 
(user_id, species_id, research_content, latitude, longitude, is_native)
VALUES 
(1, 1, 'Seen near GIKI gate', 34.07, 72.48, true),
(2, 2, 'On university rooftop', 34.08, 72.49, true),
(1, 3, 'Rare sighting near forest', 34.10, 72.52, false);

INSERT INTO forum (obs_id, user_id, comments, parent_id)
VALUES 
(1, 1, 'Interesting sighting!', NULL),
(1, 2, 'I also saw this species nearby', 1);

--testing data
select u.user_id, s.genus_name, s.species_name, o.research_content, o.latitude, o.longitude, o.observed_at
from observation o
join users u on u.user_id = o.user_id
join species s on s.species_id = o.species_id;

SELECT  * FROM observation;










