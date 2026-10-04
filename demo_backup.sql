CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    course VARCHAR(100) NOT NULL
);

INSERT INTO students (id, name, course) VALUES
(1, 'Adiba', 'Database Management'),
(2, 'Rahul', 'Cloud Computing'),
(3, 'Sara', 'Python');
