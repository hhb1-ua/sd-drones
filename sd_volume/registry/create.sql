CREATE TABLE Drone (
    identifier INT PRIMARY KEY,
    alias VARCHAR(128) NOT NULL,
    password VARCHAR(128) NOT NULL
);

CREATE TABLE Token (
    token VARCHAR(128) PRIMARY KEY,
    expiration DATETIME NOT NULL
);
