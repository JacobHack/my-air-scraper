CREATE TABLE IF NOT EXISTS raw_air_data (
    id SERIAL PRIMARY KEY,
    request_time TIMESTAMPTZ DEFAULT now(),
    location JSONB NOT NULL,
    air_data JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS locations (
    location_id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    CONSTRAINT uq_location UNIQUE (latitude, longitude)
);

CREATE TABLE IF NOT EXISTS air_quality_readings (
    reading_id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(location_id),
    datetime TIMESTAMPTZ NOT NULL,
    aqi INT NOT NULL,
    CONSTRAINT uq_reading UNIQUE (location_id, datetime)
);

CREATE TABLE IF NOT EXISTS components (
    component_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS reading_components (
    reading_id INT REFERENCES air_quality_readings(reading_id) ON DELETE CASCADE,
    component_id INT REFERENCES components(component_id) ON DELETE CASCADE,
    value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (reading_id, component_id)
);
