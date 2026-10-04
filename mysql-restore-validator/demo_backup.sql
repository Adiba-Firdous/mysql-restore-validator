-- Demo backup for mysql-restore-validator
-- Safe test data only.

CREATE DATABASE IF NOT EXISTS backup_restore_demo;
USE backup_restore_demo;

DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    course VARCHAR(100) NOT NULL
);

INSERT INTO students (id, name, course) VALUES
(1, 'Adiba', 'Database Management'),
(2, 'Rahul', 'Cloud Computing'),
(3, 'Sara', 'Python');
