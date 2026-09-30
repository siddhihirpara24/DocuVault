-- =======================================================
-- Database Schema for Personal Document Organizer
-- Suitable for MySQL 8.0+ / MariaDB
-- =======================================================

CREATE DATABASE IF NOT EXISTS `document_organizer_db` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `document_organizer_db`;

-- -------------------------------------------------------
-- 1. Table structure for table `users`
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `phone` VARCHAR(20) NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'user', -- 'user' or 'admin'
    `status` VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active' or 'inactive'
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_role` (`role`),
    INDEX `idx_users_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- 2. Table structure for table `categories`
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_categories_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- 3. Table structure for table `documents`
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS `documents` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `category_id` INT NULL,
    `document_name` VARCHAR(200) NOT NULL,
    `description` TEXT NULL,
    `original_filename` VARCHAR(255) NOT NULL,
    `stored_filename` VARCHAR(255) NOT NULL UNIQUE,
    `file_path` VARCHAR(500) NOT NULL,
    `file_type` VARCHAR(50) NOT NULL,
    `file_size` INT NOT NULL, -- in bytes
    `upload_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_documents_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_documents_category` FOREIGN KEY (`category_id`) 
        REFERENCES `categories` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX `idx_documents_user_id` (`user_id`),
    INDEX `idx_documents_category_id` (`category_id`),
    INDEX `idx_documents_file_type` (`file_type`),
    INDEX `idx_documents_upload_date` (`upload_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- 4. Table structure for table `password_reset_tokens`
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS `password_reset_tokens` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `token` VARCHAR(100) NOT NULL UNIQUE,
    `expires_at` DATETIME NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_tokens_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX `idx_tokens_token` (`token`),
    INDEX `idx_tokens_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- Initial Category Seeds
-- -------------------------------------------------------
INSERT IGNORE INTO `categories` (`id`, `name`, `description`, `created_at`) VALUES
(1, 'Education', 'Academic transcripts, marksheets, degree certificates, and grade cards.', NOW()),
(2, 'Identity', 'Passport, National ID, Driving License, Voter ID, and citizen credentials.', NOW()),
(3, 'Career', 'Resumes, CVs, Offer letters, Experience certificates, and Payslips.', NOW()),
(4, 'Financial', 'Bank statements, Tax returns, Investment proofs, and Audit slips.', NOW()),
(5, 'Bills', 'Electricity, Internet bills, Rent receipts, and Utility vouchers.', NOW()),
(6, 'Certificates', 'Professional accreditations, Training certifications, and Workshop awards.', NOW()),
(7, 'Medical', 'Health insurance policies, Prescription notes, and Diagnostic reports.', NOW()),
(8, 'Other', 'Miscellaneous personal notes, Warranties, and General documentation.', NOW());
