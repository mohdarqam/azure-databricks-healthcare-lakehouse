-- =============================================================================
-- Source system: PostgreSQL (Neon) — Meridian Health Network operational DB
-- Run this in the Neon SQL editor to create the three source tables + sample data.
-- Schema: public
-- =============================================================================

DROP TABLE IF EXISTS public.patients;
DROP TABLE IF EXISTS public.doctors;
DROP TABLE IF EXISTS public.hospitals;

-- -----------------------------------------------------------------------------
-- hospitals (full load)
-- -----------------------------------------------------------------------------
CREATE TABLE public.hospitals (
    hospital_id   INT PRIMARY KEY,
    hospital_name VARCHAR(120) NOT NULL,
    city          VARCHAR(80),
    county        VARCHAR(80),
    beds          INT,
    created_at    TIMESTAMP DEFAULT NOW()
);

INSERT INTO public.hospitals (hospital_id, hospital_name, city, county, beds) VALUES
    (1, 'Meridian General',        'Dublin',   'Dublin',    420),
    (2, 'Meridian West',           'Galway',   'Galway',    260),
    (3, 'Meridian Riverside',      'Cork',     'Cork',      310),
    (4, 'Meridian Midlands',       'Athlone',  'Westmeath', 145);

-- -----------------------------------------------------------------------------
-- doctors (full load)
-- -----------------------------------------------------------------------------
CREATE TABLE public.doctors (
    doctor_id    INT PRIMARY KEY,
    full_name    VARCHAR(120) NOT NULL,
    speciality   VARCHAR(80),
    hospital_id  INT REFERENCES public.hospitals(hospital_id),
    created_at   TIMESTAMP DEFAULT NOW()
);

INSERT INTO public.doctors (doctor_id, full_name, speciality, hospital_id) VALUES
    (101, 'Dr. Aoife Byrne',    'Cardiology',   1),
    (102, 'Dr. Sanjay Rao',     'Oncology',     1),
    (103, 'Dr. Niamh Kelly',    'Paediatrics',  2),
    (104, 'Dr. Liam Murphy',    'Orthopaedics', 3),
    (105, 'Dr. Priya Nair',     'Endocrinology',4);

-- -----------------------------------------------------------------------------
-- patients (merge / incremental load — note updated_at watermark column)
-- -----------------------------------------------------------------------------
CREATE TABLE public.patients (
    patient_id   INT PRIMARY KEY,
    full_name    VARCHAR(120) NOT NULL,
    date_of_birth DATE,
    gender       VARCHAR(20),
    hospital_id  INT REFERENCES public.hospitals(hospital_id),
    primary_doctor_id INT REFERENCES public.doctors(doctor_id),
    updated_at   TIMESTAMP DEFAULT NOW()   -- <-- watermark_column for incremental loads
);

INSERT INTO public.patients
    (patient_id, full_name, date_of_birth, gender, hospital_id, primary_doctor_id, updated_at) VALUES
    (5001, 'Patient A', '1984-03-11', 'F', 1, 101, '2026-01-05 09:00:00'),
    (5002, 'Patient B', '1979-07-22', 'M', 1, 102, '2026-01-06 09:00:00'),
    (5003, 'Patient C', '2015-11-30', 'F', 2, 103, '2026-01-07 09:00:00'),
    (5004, 'Patient D', '1968-02-14', 'M', 3, 104, '2026-01-08 09:00:00'),
    (5005, 'Patient E', '1992-09-01', 'F', 4, 105, '2026-01-09 09:00:00');

-- Quick check
-- SELECT * FROM public.hospitals;
-- SELECT * FROM public.doctors;
-- SELECT * FROM public.patients;
