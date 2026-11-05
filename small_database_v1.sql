
-- =========================================
-- 1. Create Database
-- =========================================

CREATE DATABASE clinic_system
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE clinic_system;


-- =========================================
-- 2. PATIENTS
-- =========================================

CREATE TABLE patients (
    patient_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    national_code CHAR(10) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    birth_date DATE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


-- =========================================
-- 3. USERS
-- =========================================

CREATE TABLE users (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('secretary', 'doctor', 'admin') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


-- =========================================
-- 4. APPOINTMENTS
-- =========================================

CREATE TABLE appointments (
    appointment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    created_by BIGINT NOT NULL,
    appointment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM(
        'created',
        'in_progress',
        'completed',
        'cancelled'
    ) NOT NULL DEFAULT 'created',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_appointments_patient (patient_id),
    INDEX idx_appointments_creator (created_by),
    INDEX idx_appointments_date (appointment_date),

    CONSTRAINT fk_appointments_patient
        FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_appointments_user
        FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;


-- =========================================
-- 5. AUDIO_FILES
-- =========================================

CREATE TABLE audio_files (
    audio_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    appointment_id BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    transcription LONGTEXT,
    processing_status ENUM(
        'uploaded',
        'transcribing',
        'transcribed',
        'failed'
    ) NOT NULL DEFAULT 'uploaded',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audio_appointment (appointment_id),

    CONSTRAINT fk_audio_appointment
        FOREIGN KEY (appointment_id)
        REFERENCES appointments(appointment_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;


-- =========================================
-- 6. MEDICAL_RECORDS
-- =========================================

CREATE TABLE medical_records (
    record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    appointment_id BIGINT NOT NULL UNIQUE,
    approved_by BIGINT,
    diagnosis TEXT,
    instructions TEXT,
    extraction_json JSON,
    status ENUM(
        'draft',
        'pending_review',
        'approved'
    ) NOT NULL DEFAULT 'draft',
    approved_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_records_approver (approved_by),

    CONSTRAINT fk_records_appointment
        FOREIGN KEY (appointment_id)
        REFERENCES appointments(appointment_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_records_approver
        FOREIGN KEY (approved_by)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;


-- =========================================
-- 7. MEDICATIONS
-- =========================================

CREATE TABLE medications (
    medication_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    record_id BIGINT NOT NULL,
    drug_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    duration VARCHAR(100),
    instructions TEXT,

    INDEX idx_medications_record (record_id),

    CONSTRAINT fk_medications_record
        FOREIGN KEY (record_id)
        REFERENCES medical_records(record_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;


-- =========================================
-- 8. DOCUMENTS
-- =========================================

CREATE TABLE documents (
    document_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    record_id BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    document_type ENUM(
        'medical_report',
        'prescription',
        'other'
    ) NOT NULL DEFAULT 'medical_report',
    print_status ENUM(
        'generated',
        'printed',
        'failed'
    ) NOT NULL DEFAULT 'generated',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_documents_record (record_id),

    CONSTRAINT fk_documents_record
        FOREIGN KEY (record_id)
        REFERENCES medical_records(record_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB;








CREATE USER 'clinic_app'@'localhost'
IDENTIFIED BY 'test1234';

GRANT SELECT, INSERT, UPDATE
ON clinic_system.*
TO 'clinic_app'@'localhost';

FLUSH PRIVILEGES;