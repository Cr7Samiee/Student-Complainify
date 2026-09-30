-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 30, 2026 at 03:52 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `complainify`
--

-- --------------------------------------------------------

--
-- Table structure for table `audit_logs`
--

CREATE TABLE `audit_logs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `target_type` varchar(50) DEFAULT NULL,
  `target_id` varchar(50) DEFAULT NULL,
  `details` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `audit_logs`
--

INSERT INTO `audit_logs` (`id`, `user_id`, `action`, `target_type`, `target_id`, `details`, `created_at`) VALUES
(1, 2, 'login', 'session', '', 'Admin login', '2026-07-27 16:14:20'),
(2, 2, 'update_status', 'complaint', 'CMP-0748', 'Status: In Progress', '2026-07-27 16:14:24'),
(3, 2, 'add_comment', 'complaint', 'CMP-0748', 'Our department will survey and fix your problem soon.', '2026-07-27 17:05:18'),
(4, 2, 'update_status', 'complaint', 'CMP-0748', 'Status: Resolved', '2026-07-27 17:05:31'),
(5, 2, 'update_status', 'complaint', 'CMP-0748', 'Status: Resolved', '2026-07-27 17:05:52'),
(6, 5, 'login', 'session', '', 'Student login', '2026-07-27 17:06:14'),
(7, 5, 'login', 'session', '', 'Student login', '2026-07-27 17:07:03'),
(8, 5, 'submit_complaint', 'complaint', 'CMP-532B', 'Category: Security, Priority: High', '2026-07-27 17:08:52'),
(9, 2, 'login', 'session', '', 'Admin login', '2026-07-27 17:10:40'),
(10, 2, 'validate_complaint', 'complaint', 'CMP-532B', '', '2026-07-27 17:11:04'),
(11, 2, 'update_status', 'complaint', 'CMP-532B', 'Status: In Progress', '2026-07-27 17:12:08'),
(12, 2, 'update_status', 'complaint', 'CMP-532B', 'Status: Resolved', '2026-07-27 17:13:29'),
(13, 2, 'login', 'session', '', 'Admin login', '2026-07-27 17:14:19'),
(14, 2, 'update_status', 'complaint', 'CMP-532B', 'Status: Resolved', '2026-07-27 17:14:39'),
(15, NULL, 'submit_complaint', 'complaint', 'CMP-DA51', 'Category: Academics, Priority: Medium', '2026-07-27 17:19:38'),
(16, 5, 'login', 'session', '', 'Student login', '2026-07-31 15:35:37'),
(17, 5, 'submit_complaint', 'complaint', 'CMP-36B7', 'Category: Security, Priority: High', '2026-07-31 15:37:04'),
(18, 2, 'login', 'session', '', 'Admin login', '2026-07-31 15:41:17'),
(19, 2, 'validate_complaint', 'complaint', 'CMP-36B7', '', '2026-07-31 15:43:19'),
(20, 2, 'update_status', 'complaint', 'CMP-36B7', 'Status: In Progress', '2026-07-31 15:43:37'),
(21, 2, 'update_status', 'complaint', 'CMP-36B7', 'Status: Resolved', '2026-07-31 15:45:05'),
(22, 5, 'submit_complaint', 'complaint', 'CMP-3E6C', 'Category: Administrative, Priority: High', '2026-07-31 15:46:10'),
(23, 2, 'login', 'session', '', 'Admin login', '2026-07-31 16:06:35'),
(24, 2, 'login', 'session', '', 'Admin login', '2026-07-31 16:20:44'),
(25, 2, 'import_csv', 'complaint', NULL, 'Imported 2 complaint(s) from CSV', '2026-07-31 17:13:15'),
(26, NULL, 'submit_complaint', 'complaint', 'CMP-4759', 'Category: Academics, Priority: Medium', '2026-08-07 14:49:47'),
(27, 2, 'login', 'session', '', 'Admin login', '2026-08-07 14:50:48'),
(28, 2, 'retrain_model', 'model', '', '', '2026-08-07 14:53:27'),
(29, 2, 'validate_complaint', 'complaint', 'CMP-4759', '', '2026-08-07 14:53:57'),
(30, 2, 'confirm_label', 'complaint', 'CMP-4759', 'Confirmed category: Academics', '2026-08-07 14:54:13'),
(31, NULL, 'submit_complaint', 'complaint', 'CMP-6790', 'Category: Academics, Priority: High', '2026-08-07 14:58:24'),
(32, 2, 'login', 'session', '', 'Admin login', '2026-08-07 15:15:45'),
(33, 2, 'validate_complaint', 'complaint', 'CMP-6790', '', '2026-08-07 15:16:55'),
(34, 2, 'add_comment', 'complaint', 'CMP-6790', 'Send to the Department.', '2026-08-07 15:17:20'),
(35, 2, 'retrain_model', 'model', '', '', '2026-08-07 15:17:49'),
(36, 2, 'login', 'session', '', 'Admin login', '2026-08-07 15:19:22'),
(37, 2, 'submit_complaint', 'complaint', 'CMP-2A60', 'Category: IT Support, Priority: High', '2026-08-08 02:44:50'),
(38, 5, 'login', 'session', '', 'Student login', '2026-08-08 02:51:31'),
(39, 5, 'submit_complaint', 'complaint', 'CMP-3015', 'Category: Canteen, Priority: High', '2026-08-08 02:53:06'),
(40, 2, 'login', 'session', '', 'Admin login', '2026-08-08 02:54:10'),
(41, 2, 'confirm_label', 'complaint', 'CMP-3015', 'Confirmed category: Canteen', '2026-08-08 02:54:29'),
(42, 2, 'retrain_model', 'model', '', '', '2026-08-08 02:54:43'),
(43, NULL, 'submit_complaint', 'complaint', 'CMP-BDB1', 'Category: Academic, Priority: Medium', '2026-08-08 03:08:23'),
(44, NULL, 'submit_complaint', 'complaint', 'CMP-F95B', 'Category: General, Priority: Low', '2026-08-08 03:08:23'),
(45, NULL, 'submit_complaint', 'complaint', 'CMP-5A20', 'Category: Academic, Priority: Low', '2026-08-08 03:08:23'),
(46, NULL, 'submit_complaint', 'complaint', 'CMP-E2B1', 'Category: Academics, Priority: Low', '2026-08-08 06:07:00'),
(47, NULL, 'submit_complaint', 'complaint', 'CMP-E1F3', 'Category: Security, Priority: Medium', '2026-08-08 06:08:28'),
(48, NULL, 'submit_complaint', 'complaint', 'CMP-0D3E', 'Category: Academics, Priority: Low', '2026-08-08 06:09:46'),
(49, NULL, 'submit_complaint', 'complaint', 'CMP-327F', 'Category: Academics, Priority: Medium', '2026-08-08 06:11:35'),
(50, NULL, 'submit_complaint', 'complaint', 'CMP-0FFD', 'Category: Academics, Priority: Medium', '2026-08-08 06:11:42'),
(51, NULL, 'submit_complaint', 'complaint', 'CMP-EEAC', 'Category: Academics, Priority: Medium', '2026-08-08 06:12:46'),
(52, NULL, 'submit_complaint', 'complaint', 'CMP-82FB', 'Category: Academics, Priority: Medium', '2026-08-08 06:15:33'),
(53, 2, 'login', 'session', '', 'Admin login', '2026-08-08 06:33:47'),
(54, NULL, 'submit_complaint', 'complaint', 'CMP-C3A6', 'Category: IT Support, Priority: Medium', '2026-08-08 07:07:33'),
(55, 2, 'login', 'session', '', 'Admin login', '2026-08-08 07:08:02'),
(56, 2, 'confirm_label', 'complaint', 'CMP-C3A6', 'Confirmed category: IT Support', '2026-08-08 07:09:53'),
(57, 2, 'retrain_model', 'model', '', '', '2026-08-08 07:35:37'),
(58, 2, 'login', 'session', '', 'Admin login', '2026-08-08 15:52:43'),
(59, NULL, 'submit_complaint', 'complaint', 'CMP-9AFC', 'Category: Security, Priority: High', '2026-08-09 08:14:07'),
(60, NULL, 'submit_complaint', 'complaint', 'CMP-3E1F', 'Category: Administrative, Priority: Medium', '2026-08-09 08:16:22'),
(61, 2, 'login', 'session', '', 'Admin login', '2026-08-09 08:16:58'),
(62, NULL, 'submit_complaint', 'complaint', 'CMP-3E5F', 'Category: Administrative, Priority: Medium', '2026-08-09 08:27:53'),
(63, 2, 'login', 'session', '', 'Admin login', '2026-08-09 08:28:17'),
(64, NULL, 'submit_complaint', 'complaint', 'CMP-9669', 'Category: Security, Priority: High', '2026-08-13 06:31:21'),
(65, 2, 'login', 'session', '', 'Admin login', '2026-09-26 17:00:29'),
(66, 2, 'retrain_model', 'model', '', '', '2026-09-26 17:05:40'),
(67, 2, 'retrain_model', 'model', '', '', '2026-09-26 17:05:52'),
(68, 2, 'login', 'session', '', 'Admin login', '2026-09-26 17:22:59'),
(69, 6, 'login', 'session', '', 'Student login', '2026-09-27 04:18:41'),
(70, 6, 'submit_complaint', 'complaint', 'CMP-F0C7', 'Category: Other, Priority: High', '2026-09-27 04:20:21'),
(71, 2, 'login', 'session', '', 'Admin login', '2026-09-27 04:51:21'),
(72, 2, 'update_status', 'complaint', 'CMP-F0C7', 'Status: In Progress', '2026-09-27 04:52:28'),
(73, 2, 'update_status', 'complaint', 'CMP-F0C7', 'Status: In Progress', '2026-09-27 04:52:44'),
(74, 2, 'validate_complaint', 'complaint', 'CMP-F0C7', '', '2026-09-27 04:53:34'),
(75, 2, 'update_status', 'complaint', 'CMP-F0C7', 'Status: In Progress', '2026-09-27 04:53:51'),
(76, 2, 'confirm_label', 'complaint', 'CMP-F0C7', 'Confirmed category: Academics', '2026-09-27 04:54:39'),
(77, 2, 'update_status', 'complaint', 'CMP-F0C7', 'Status: Resolved', '2026-09-27 04:54:41'),
(78, 2, 'update_status', 'complaint', 'CMP-F0C7', 'Status: Resolved', '2026-09-27 04:55:00'),
(79, 6, 'add_comment', 'complaint', 'CMP-F0C7', 'Thank you sir', '2026-09-27 04:55:48'),
(80, NULL, 'submit_complaint', 'complaint', 'CMP-CA15', 'Category: Canteen, Priority: High', '2026-09-27 04:57:43'),
(81, 2, 'validate_complaint', 'complaint', 'CMP-CA15', '', '2026-09-27 04:58:47'),
(82, 2, 'confirm_label', 'complaint', 'CMP-CA15', 'Confirmed category: Canteen', '2026-09-27 04:58:50'),
(83, 2, 'update_status', 'complaint', 'CMP-CA15', 'Status: Pending', '2026-09-27 04:58:54'),
(84, 2, 'update_status', 'complaint', 'CMP-CA15', 'Status: Resolved', '2026-09-27 04:59:58'),
(85, 2, 'retrain_model', 'model', '', '', '2026-09-27 05:00:03');

-- --------------------------------------------------------

--
-- Table structure for table `colleges`
--

CREATE TABLE `colleges` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `colleges`
--

INSERT INTO `colleges` (`id`, `name`) VALUES
(6, 'College of Education'),
(3, 'College of Engineering'),
(1, 'College of Science & Technology'),
(4, 'Faculty of Health Sciences'),
(5, 'Faculty of Humanities & Social Sciences'),
(7, 'Faculty of Law'),
(8, 'Other'),
(2, 'School of Business & Management');

-- --------------------------------------------------------

--
-- Table structure for table `complaints`
--

CREATE TABLE `complaints` (
  `id` int(11) NOT NULL,
  `ticket_id` varchar(20) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `fullname` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `college` varchar(100) DEFAULT NULL,
  `category` varchar(50) NOT NULL,
  `priority` enum('Low','Medium','High') NOT NULL DEFAULT 'Medium',
  `priority_score` int(11) DEFAULT 0,
  `priority_reason` varchar(255) DEFAULT NULL,
  `subject` varchar(200) NOT NULL,
  `description` text DEFAULT NULL,
  `status` enum('Pending','In Progress','Resolved') NOT NULL DEFAULT 'Pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `assigned_to` varchar(100) DEFAULT NULL,
  `assigned_at` datetime DEFAULT NULL,
  `resolved_at` datetime DEFAULT NULL,
  `admin_notes` text DEFAULT NULL,
  `validated` tinyint(1) DEFAULT 0,
  `email_sent` tinyint(1) DEFAULT 0,
  `sentiment` varchar(20) DEFAULT 'Neutral',
  `sentiment_score` float DEFAULT 0,
  `attachment` varchar(255) DEFAULT NULL,
  `student_attachment` varchar(255) DEFAULT NULL,
  `model_version` varchar(20) DEFAULT NULL,
  `category_confirmed` tinyint(1) DEFAULT 0,
  `confirmed_by` varchar(100) DEFAULT NULL,
  `confirmed_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `complaints`
--

INSERT INTO `complaints` (`id`, `ticket_id`, `user_id`, `fullname`, `email`, `college`, `category`, `priority`, `priority_score`, `priority_reason`, `subject`, `description`, `status`, `created_at`, `assigned_to`, `assigned_at`, `resolved_at`, `admin_notes`, `validated`, `email_sent`, `sentiment`, `sentiment_score`, `attachment`, `student_attachment`, `model_version`, `category_confirmed`, `confirmed_by`, `confirmed_at`) VALUES
(4, 'CMP-2831', NULL, 'Test', 'test@test.com', NULL, 'IT Support', 'High', 0, NULL, 'Test WiFi', 'WiFi is broken', 'Pending', '2026-07-21 14:39:20', NULL, NULL, NULL, NULL, 0, 0, 'Negative', -2, NULL, NULL, NULL, 0, NULL, NULL),
(5, 'CMP-AAF5', 3, 'Samir Poudel', 'abc@gmail.com', NULL, 'Academics', 'Medium', 0, NULL, 'Teacher doesnt teach us good in computer Science', 'Our teacher doesnt teach us course related task as he just teach us 10 minutes and talk about another subject matter', 'Resolved', '2026-07-23 11:45:37', 'Academic Affairs', '2026-07-23 17:32:14', '2026-07-23 17:34:56', 'We will vusit your college soon.', 1, 1, 'Positive', 1, 'CMP-AAF5_e0b6bb40.png', NULL, NULL, 0, NULL, NULL),
(6, 'CMP-EAF4', NULL, 'ANON-7FB978B5', 'anon-7fb978b5@anonymous.complainify', NULL, 'Canteen', 'Medium', 0, NULL, 'Slate Food', 'I found the coachroach poops in  college food canteen. For the inspection see in below uploaded file.', 'Pending', '2026-07-23 12:50:03', NULL, NULL, NULL, NULL, 0, 0, 'Neutral', 0, NULL, NULL, NULL, 0, NULL, NULL),
(7, 'CMP-5BE3', 1, 'Ram Sharma', 'ram@gmail.com', NULL, 'Academics', 'High', 0, NULL, 'Test academic complaint', 'This is a test academic complaint for layout verification.', 'Pending', '2026-07-23 14:44:31', NULL, NULL, NULL, NULL, 0, 1, 'Negative', -1, NULL, NULL, NULL, 0, NULL, NULL),
(8, 'CMP-17E6', 5, 'Samirr Poudel', 'cr7samiee@gmail.com', NULL, 'Canteen', 'Medium', 0, NULL, 'Canteen Food Quality', 'I found the piece of hair in the food in the college canteen. Please resolve this problem now', 'Resolved', '2026-07-27 15:21:18', 'Canteen', '2026-07-27 21:29:46', '2026-07-27 21:32:58', '', 0, 1, 'Neutral', 0, 'CMP-17E6_db215aad.png', NULL, NULL, 0, NULL, NULL),
(9, 'CMP-0748', NULL, 'ANON-6E356391', 'anon-6e356391@anonymous.complainify', NULL, 'IT Support', 'High', 0, NULL, 'Internet Connection issue', 'In my college ethernet is not being working. I have complained many time to college department bu they didnt obey us . Please resolve ethernet problem soon', 'Resolved', '2026-07-27 15:57:20', 'IT Support', '2026-07-27 21:42:20', '2026-07-27 22:50:46', 'Our department will be reach put soon', 1, 0, 'Negative', -0.333, NULL, NULL, NULL, 0, NULL, NULL),
(10, 'CMP-532B', 5, 'Samirr Poudel', 'cr7samiee@gmail.com', NULL, 'Security', 'High', 0, NULL, 'Stole my instruments', 'Someone has stole my geometry box during tiffin time . Before tiffin time it was in my bag but when I came back I found there was no geometry box. Please resolve this. I have uploaded you my box pics.', 'Resolved', '2026-07-27 17:08:52', 'Security', '2026-07-27 22:53:52', '2026-07-27 22:59:34', 'We have found your box please come and collect in rection . Thank you.', 1, 1, 'Negative', -0.1, NULL, 'CMP-532B_e7fc5b3b.png', NULL, 0, NULL, NULL),
(11, 'CMP-DA51', NULL, 'ANON-48CE16B6', 'anon-48ce16b6@anonymous.complainify', NULL, 'Academics', 'Medium', 0, NULL, 'Program Feedback', 'The program which conducted by our IT deparmtent was informative. But I would suggest small suggestion like audio visuals were not clear.', 'In Progress', '2026-07-27 17:19:37', 'Academics', '2026-07-27 23:04:37', NULL, NULL, 0, 0, 'Positive', 0.121, NULL, NULL, NULL, 0, NULL, NULL),
(12, 'CMP-36B7', 5, 'Samir Poudel', 'cr7samiee@gmail.com', NULL, 'Security', 'High', 0, NULL, 'Student Harrasmenet', 'Teacher sexually harass one student of my class . Please take legal action', 'Resolved', '2026-07-31 15:37:04', 'Security', '2026-07-31 21:22:04', '2026-07-31 21:29:59', 'Information is attached here', 1, 1, 'Negative', -0.103, 'CMP-36B7_ff847d9c.png', NULL, NULL, 0, NULL, NULL),
(13, 'CMP-3E6C', 5, 'Samir Poudel', 'cr7samiee@gmail.com', NULL, 'Administrative', 'High', 0, NULL, 'Student Harrasmenet', 'Today exhibition was good. But somehow management was poor.', 'In Progress', '2026-07-31 15:46:10', 'Administrative', '2026-07-31 21:31:10', NULL, NULL, 0, 1, 'Negative', -0.494, NULL, NULL, NULL, 0, NULL, NULL),
(16, 'CMP-4759', NULL, 'ANON-B9C7FF98', 'anon-b9c7ff98@anonymous.complainify', NULL, 'Academics', 'Medium', 0, NULL, 'Teacher Issue', 'Teacher doesn;t teach us syllabus contents. I have upload u file you can review it..', 'In Progress', '2026-08-07 14:49:47', 'Academics', '2026-08-07 20:34:47', NULL, NULL, 1, 0, 'Neutral', 0, NULL, NULL, 'v20260807_200210', 1, 'Admin User', '2026-08-07 20:39:13'),
(17, 'CMP-6790', NULL, 'ANON-D2EC8EA2', 'anon-d2ec8ea2@anonymous.complainify', NULL, 'Academics', 'High', 0, NULL, 'Student Beaten', 'Teacher beat one student badly and he used offensive words to the student because of that he is crying and scare to come school because of the teacher behavior. Please take legal action against teacher.', 'In Progress', '2026-08-07 14:58:24', 'Academics', '2026-08-07 20:43:24', NULL, NULL, 1, 0, 'Negative', -0.908, NULL, NULL, 'v20260807_203827', 0, NULL, NULL),
(19, 'CMP-1024', 1, 'Ram Sharma', 'ram@gmail.com', NULL, 'Academics', 'High', 0, NULL, 'Missing Semester Credits', 'I am missing 2 credits from last semester transcript.', 'Pending', '2026-08-07 15:44:33', NULL, NULL, NULL, NULL, 0, 0, 'Negative', -1.5, NULL, NULL, NULL, 0, NULL, NULL),
(20, 'CMP-1023', 1, 'Ram Sharma', 'ram@gmail.com', NULL, 'Hostels', 'Medium', 0, NULL, 'Hostel Water Issue', 'No hot water in Block C since 2 days.', 'In Progress', '2026-08-07 15:44:33', NULL, NULL, NULL, NULL, 0, 0, 'Negative', -2, NULL, NULL, NULL, 0, NULL, NULL),
(21, 'CMP-1022', 1, 'Ram Sharma', 'ram@gmail.com', NULL, 'IT Support', 'Low', 0, NULL, 'WiFi Connectivity', 'Library WiFi is very slow.', 'Resolved', '2026-08-07 15:44:33', NULL, NULL, NULL, NULL, 0, 0, 'Neutral', 0, NULL, NULL, NULL, 0, NULL, NULL),
(22, 'CMP-2A60', 2, 'Admin User', 'admin@complainify.edu', 'College of Science & Technology', 'IT Support', 'High', 0, NULL, 'Wifi problem ', 'The wifi hasn\'t been rinning in canteen which make us difficulty for payement. Please fix this.', 'In Progress', '2026-08-08 02:44:50', 'IT Support', '2026-08-08 08:29:50', NULL, NULL, 0, 0, 'Negative', -0.421, NULL, NULL, 'v20260808_080626', 0, NULL, NULL),
(23, 'CMP-3015', 5, 'Samirr Poudel', 'cr7samiee@gmail.com', 'College of Engineering', 'Canteen', 'High', 0, NULL, 'Canteen Staff Rude Behaviour', 'A new canteen staff is behaving us rude. Please take the action quickly.', 'In Progress', '2026-08-08 02:53:06', 'Canteen', '2026-08-08 08:38:06', NULL, NULL, 0, 1, 'Negative', -0.572, NULL, NULL, 'v20260808_080626', 1, 'Admin User', '2026-08-08 08:39:29'),
(24, 'CMP-BDB1', NULL, 'Anonymous', '', NULL, 'Academic', 'Medium', 2, 'negative tone, urgent issue', 'WiFi not working in hostel since morning', 'The wifi in hostel block B has not been working since morning, please fix it asap, I have a deadline tomorrow', 'Pending', '2026-08-08 03:08:23', NULL, NULL, NULL, NULL, 0, 0, 'Negative', -0.153, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(25, 'CMP-F95B', NULL, 'Anonymous', '', NULL, 'General', 'Low', 0, 'positive tone', 'Thank you for the quick help', 'Thank you so much, my problem was solved and staff were very helpful, I appreciate the quick response', 'Pending', '2026-08-08 03:08:23', NULL, NULL, NULL, NULL, 0, 0, 'Positive', 0.898, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(26, 'CMP-5A20', NULL, 'Anonymous', '', NULL, 'Academic', 'Low', 0, 'baseline', 'Syllabus request', 'please share the syllabus for the next term when you get a chance', 'Pending', '2026-08-08 03:08:23', NULL, NULL, NULL, NULL, 0, 0, 'Neutral', 0, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(27, 'CMP-E2B1', NULL, 'ANON-1E4028C2', 'anon-1e4028c2@anonymous.complainify', 'College of Engineering', 'Academics', 'Low', 0, 'baseline', 'Teacher Change', 'the professor isn\'t aligned with the course and syllabus.', 'In Progress', '2026-08-08 06:07:00', 'Academics', '2026-08-08 11:52:00', NULL, NULL, 0, 0, 'Neutral', 0, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(28, 'CMP-E1F3', NULL, 'ANON-2F028F42', 'anon-2f028f42@anonymous.complainify', 'College of Science & Technology', 'Security', 'Medium', 2, 'strong negative tone', 'Reconstruction', 'Our building was destroyed in fire', 'In Progress', '2026-08-08 06:08:27', 'Security', '2026-08-08 11:53:27', NULL, NULL, 0, 0, 'Negative', -0.681, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(29, 'CMP-0D3E', NULL, 'ANON-6D940DA2', 'anon-6d940da2@anonymous.complainify', 'College of Engineering', 'Academics', 'Low', 0, 'baseline', 'College Infrastructure', 'The quality of projector is not good in our classroom. Please remove it.', 'In Progress', '2026-08-08 06:09:46', 'Academics', '2026-08-08 11:54:46', NULL, NULL, 0, 0, 'Neutral', -0.027, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(30, 'CMP-327F', NULL, 'ANON-4959E92D', 'anon-4959e92d@anonymous.complainify', NULL, 'Academics', 'Medium', 2, 'strong negative tone', 'Teacher Issue', 'Teacher beat badly to the student without any reason. Please take the actions.', 'In Progress', '2026-08-08 06:11:35', 'Academics', '2026-08-08 11:56:35', NULL, NULL, 0, 0, 'Negative', -0.62, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(31, 'CMP-0FFD', NULL, 'ANON-721607DE', 'anon-721607de@anonymous.complainify', 'College of Engineering', 'Academics', 'Medium', 2, 'strong negative tone', 'Teacher Issue', 'Teacher beat badly to the student without any reason. Please take the actions.', 'In Progress', '2026-08-08 06:11:41', 'Academics', '2026-08-08 11:56:41', NULL, NULL, 0, 0, 'Negative', -0.62, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(32, 'CMP-EEAC', NULL, 'ANON-28F6DA5F', 'anon-28f6da5f@anonymous.complainify', 'College of Science & Technology', 'Academics', 'Medium', 2, 'strong negative tone', 'Teacher Issue', 'Teacher beat the student badly to the student', 'In Progress', '2026-08-08 06:12:45', 'Academics', '2026-08-08 11:57:45', NULL, NULL, 0, 0, 'Negative', -0.477, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(33, 'CMP-82FB', NULL, 'ANON-E416ED9D', 'anon-e416ed9d@anonymous.complainify', 'Faculty of Health Sciences', 'Academics', 'Medium', 2, 'strong negative tone', 'Teacher Issue', 'Teacher beat the student badly', 'In Progress', '2026-08-08 06:15:33', 'Academics', '2026-08-08 12:00:33', NULL, NULL, 0, 0, 'Negative', -0.477, NULL, NULL, 'v20260808_083943', 0, NULL, NULL),
(34, 'CMP-C3A6', NULL, 'ANON-7E7556E8', 'anon-7e7556e8@anonymous.complainify', 'College of Engineering', 'IT Support', 'Medium', 1, 'negative tone', 'Internet Connection issue', 'I am not being able to access internet in class. Please fix the internet problem.', 'In Progress', '2026-08-08 07:07:33', 'IT Support', '2026-08-08 12:52:33', NULL, NULL, 0, 0, 'Negative', -0.103, NULL, NULL, 'v20260808_083943', 1, 'Admin User', '2026-08-08 12:54:53'),
(35, 'CMP-9AFC', NULL, 'ANON-34BDFF41', 'anon-34bdff41@anonymous.complainify', 'Faculty of Health Sciences', 'Security', 'High', 3, 'Multinomial NB model (confidence 100%)', 'Ragging in College', 'Our seniors ragged my friend outside calling to the ground and sexual assault to her. Please take legal action.', 'In Progress', '2026-08-09 08:14:07', 'Security', '2026-08-09 13:59:07', NULL, NULL, 0, 0, 'Negative', -0.7, NULL, NULL, 'v20260808_132037', 0, NULL, NULL),
(36, 'CMP-3E1F', NULL, 'ANON-E411B77A', 'anon-e411b77a@anonymous.complainify', NULL, 'Administrative', 'Medium', 2, 'Multinomial NB model (confidence 100%)', 'Exhibition Management', 'The college exhibition was conducted good our college. But I saw issue like some student facing issue like water not getting on time, Wi-Fi issue. This need to be fix.', 'In Progress', '2026-08-09 08:16:22', 'Administrative', '2026-08-09 14:01:22', NULL, NULL, 0, 0, 'Negative', -1, NULL, NULL, 'v20260808_132037', 0, NULL, NULL),
(37, 'CMP-3E5F', NULL, 'ANON-A85034B9', 'anon-a85034b9@anonymous.complainify', NULL, 'Administrative', 'Medium', 2, 'Multinomial NB model (confidence 100%)', 'Exhibition Management', 'The college exhibition was conducted good our college. But I saw issue like some student facing issue like water not getting on time, Wi-Fi issue.', 'In Progress', '2026-08-09 08:27:52', 'Administrative', '2026-08-09 14:12:52', NULL, NULL, 0, 0, 'Negative', -1, NULL, NULL, 'v20260808_132037', 0, NULL, NULL),
(38, 'CMP-9669', NULL, 'ANON-A7534F10', 'anon-a7534f10@anonymous.complainify', NULL, 'Security', 'High', 3, 'flagged as anomalous', 'Brain Stolen', 'Someone stole my friend bhavishek mind.', 'In Progress', '2026-08-13 06:31:21', 'Security', '2026-08-13 12:16:21', NULL, NULL, 0, 0, 'Negative', -0.7, NULL, NULL, 'v20260808_132037', 0, NULL, NULL),
(39, 'CMP-F0C7', 6, 'Goli Bar', 'golibar26@gmail.com', 'College of Engineering', 'Academics', 'High', 3, 'Multinomial NB model (confidence 100%)', 'Harashment', 'Some one harrashed my friend , She is Crying. Should be take legal action', 'Resolved', '2026-09-27 04:20:21', NULL, NULL, '2026-09-27 10:39:53', '', 1, 1, 'Neutral', 0, 'CMP-F0C7_748cb5b4.pdf', NULL, 'v20260926_225052', 1, 'Admin User', '2026-09-27 10:39:39'),
(40, 'CMP-CA15', NULL, 'ANON-89266007', 'anon-89266007@anonymous.complainify', 'Faculty of Health Sciences', 'Canteen', 'High', 3, 'Multinomial NB model (confidence 98%)', 'Canteen Food Stale', 'I found the coachroach in canteen food today ,', 'Resolved', '2026-09-27 04:57:43', 'Canteen', '2026-09-27 10:42:43', '2026-09-27 10:44:49', 'We already took the action , Dont Worry', 1, 0, 'Negative', -0.7, NULL, NULL, 'v20260926_225052', 1, 'Admin User', '2026-09-27 10:43:50');

-- --------------------------------------------------------

--
-- Table structure for table `complaint_comments`
--

CREATE TABLE `complaint_comments` (
  `id` int(11) NOT NULL,
  `complaint_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `message` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `complaint_comments`
--

INSERT INTO `complaint_comments` (`id`, `complaint_id`, `user_id`, `message`, `created_at`) VALUES
(1, 7, 1, 'This is a test comment.', '2026-07-23 14:46:01'),
(2, 9, 2, 'Our department will survey and fix your problem soon.', '2026-07-27 17:05:18'),
(3, 17, 2, 'Send to the Department.', '2026-08-07 15:17:20'),
(4, 39, 6, 'Thank you sir', '2026-09-27 04:55:48');

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `message` text NOT NULL,
  `link` varchar(255) DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `message`, `link`, `is_read`, `created_at`) VALUES
(1, 2, 'New complaint #CMP-EAF4 (Canteen)', '/admin/complaint/CMP-EAF4', 1, '2026-07-23 12:50:03'),
(2, 2, 'New complaint #CMP-5BE3 (Academics)', '/admin/complaint/CMP-5BE3', 1, '2026-07-23 14:44:31'),
(3, 2, 'New comment on #CMP-5BE3', '/admin/complaint/CMP-5BE3', 1, '2026-07-23 14:46:01'),
(4, 2, 'New complaint #CMP-17E6 (Canteen)', '/admin/complaint/CMP-17E6', 1, '2026-07-27 15:21:18'),
(5, 5, 'Your complaint #CMP-17E6 was assigned to Canteen', '/student/complaint/CMP-17E6', 0, '2026-07-27 15:44:52'),
(6, 5, 'Your complaint #CMP-17E6 status: In Progress', '/student/complaint/CMP-17E6', 0, '2026-07-27 15:47:37'),
(7, 5, 'Your complaint #CMP-17E6 status: Resolved', '/student/complaint/CMP-17E6', 0, '2026-07-27 15:48:03'),
(8, 2, 'New complaint #CMP-0748 (IT Support)', '/admin/complaint/CMP-0748', 1, '2026-07-27 15:57:20'),
(9, 2, 'New complaint #CMP-532B (Security)', '/admin/complaint/CMP-532B', 1, '2026-07-27 17:08:52'),
(10, 5, 'Your complaint #CMP-532B was validated as legitimate', '/student/complaint/CMP-532B', 0, '2026-07-27 17:11:04'),
(11, 5, 'Your complaint #CMP-532B status: In Progress', '/student/complaint/CMP-532B', 0, '2026-07-27 17:12:08'),
(12, 5, 'Your complaint #CMP-532B status: Resolved', '/student/complaint/CMP-532B', 0, '2026-07-27 17:13:29'),
(13, 5, 'Your complaint #CMP-532B status: Resolved', '/student/complaint/CMP-532B', 0, '2026-07-27 17:14:39'),
(14, 2, 'New complaint #CMP-DA51 (Academics)', '/admin/complaint/CMP-DA51', 1, '2026-07-27 17:19:37'),
(15, 2, 'New complaint #CMP-36B7 (Security)', '/admin/complaint/CMP-36B7', 1, '2026-07-31 15:37:04'),
(16, 5, 'Your complaint #CMP-36B7 was validated as legitimate', '/student/complaint/CMP-36B7', 0, '2026-07-31 15:43:19'),
(17, 5, 'Your complaint #CMP-36B7 status: In Progress', '/student/complaint/CMP-36B7', 0, '2026-07-31 15:43:37'),
(18, 5, 'Your complaint #CMP-36B7 status: Resolved', '/student/complaint/CMP-36B7', 0, '2026-07-31 15:45:05'),
(19, 2, 'New complaint #CMP-3E6C (Administrative)', '/admin/complaint/CMP-3E6C', 1, '2026-07-31 15:46:10'),
(20, 2, 'New complaint #CMP-4759 (Academics)', '/admin/complaint/CMP-4759', 1, '2026-08-07 14:49:47'),
(21, 2, 'New complaint #CMP-6790 (Academics)', '/admin/complaint/CMP-6790', 1, '2026-08-07 14:58:24'),
(22, 2, 'New complaint #CMP-2A60 (IT Support)', '/admin/complaint/CMP-2A60', 1, '2026-08-08 02:44:50'),
(23, 2, 'New complaint #CMP-3015 (Canteen)', '/admin/complaint/CMP-3015', 0, '2026-08-08 02:53:06'),
(24, 2, 'New complaint #CMP-BDB1 (Academic)', '/admin/complaint/CMP-BDB1', 0, '2026-08-08 03:08:23'),
(25, 2, 'New complaint #CMP-F95B (General)', '/admin/complaint/CMP-F95B', 0, '2026-08-08 03:08:23'),
(26, 2, 'New complaint #CMP-5A20 (Academic)', '/admin/complaint/CMP-5A20', 0, '2026-08-08 03:08:23'),
(27, 2, 'New complaint #CMP-E2B1 (Academics)', '/admin/complaint/CMP-E2B1', 0, '2026-08-08 06:07:00'),
(28, 2, 'New complaint #CMP-E1F3 (Security)', '/admin/complaint/CMP-E1F3', 0, '2026-08-08 06:08:28'),
(29, 2, 'New complaint #CMP-0D3E (Academics)', '/admin/complaint/CMP-0D3E', 0, '2026-08-08 06:09:46'),
(30, 2, 'New complaint #CMP-327F (Academics)', '/admin/complaint/CMP-327F', 0, '2026-08-08 06:11:35'),
(31, 2, 'New complaint #CMP-0FFD (Academics)', '/admin/complaint/CMP-0FFD', 0, '2026-08-08 06:11:42'),
(32, 2, 'New complaint #CMP-EEAC (Academics)', '/admin/complaint/CMP-EEAC', 0, '2026-08-08 06:12:46'),
(33, 2, 'New complaint #CMP-82FB (Academics)', '/admin/complaint/CMP-82FB', 0, '2026-08-08 06:15:33'),
(34, 2, 'New complaint #CMP-C3A6 (IT Support)', '/admin/complaint/CMP-C3A6', 0, '2026-08-08 07:07:33'),
(35, 2, 'New complaint #CMP-9AFC (Security)', '/admin/complaint/CMP-9AFC', 0, '2026-08-09 08:14:07'),
(36, 2, 'New complaint #CMP-3E1F (Administrative)', '/admin/complaint/CMP-3E1F', 0, '2026-08-09 08:16:22'),
(37, 2, 'New complaint #CMP-3E5F (Administrative)', '/admin/complaint/CMP-3E5F', 0, '2026-08-09 08:27:53'),
(38, 2, 'New complaint #CMP-9669 (Security)', '/admin/complaint/CMP-9669', 0, '2026-08-13 06:31:21'),
(39, 2, 'New complaint #CMP-F0C7 (Other)', '/admin/complaint/CMP-F0C7', 0, '2026-09-27 04:20:21'),
(40, 6, 'Your complaint #CMP-F0C7 status: In Progress', '/student/complaint/CMP-F0C7', 0, '2026-09-27 04:52:28'),
(41, 6, 'Your complaint #CMP-F0C7 status: In Progress', '/student/complaint/CMP-F0C7', 0, '2026-09-27 04:52:44'),
(42, 6, 'Your complaint #CMP-F0C7 was validated as legitimate', '/student/complaint/CMP-F0C7', 0, '2026-09-27 04:53:34'),
(43, 6, 'Your complaint #CMP-F0C7 status: In Progress', '/student/complaint/CMP-F0C7', 0, '2026-09-27 04:53:51'),
(44, 6, 'Your complaint #CMP-F0C7 status: Resolved', '/student/complaint/CMP-F0C7', 0, '2026-09-27 04:54:41'),
(45, 6, 'Your complaint #CMP-F0C7 status: Resolved', '/student/complaint/CMP-F0C7', 0, '2026-09-27 04:55:00'),
(46, 2, 'New comment on #CMP-F0C7', '/admin/complaint/CMP-F0C7', 0, '2026-09-27 04:55:48'),
(47, 2, 'New complaint #CMP-CA15 (Canteen)', '/admin/complaint/CMP-CA15', 0, '2026-09-27 04:57:43');

-- --------------------------------------------------------

--
-- Table structure for table `otps`
--

CREATE TABLE `otps` (
  `id` int(11) NOT NULL,
  `email` varchar(100) NOT NULL,
  `otp` varchar(6) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `expires_at` datetime NOT NULL,
  `used` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `otps`
--

INSERT INTO `otps` (`id`, `email`, `otp`, `created_at`, `expires_at`, `used`) VALUES
(1, 'ram@gmail.com', '369138', '2026-07-21 14:37:05', '2026-07-21 20:32:05', 0),
(2, 'ram@gmail.com', '881533', '2026-07-21 14:39:20', '2026-07-21 20:34:20', 0);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `fullname` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `plain_password` varchar(100) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('student','admin') NOT NULL DEFAULT 'student',
  `college` varchar(100) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `fullname`, `email`, `phone`, `plain_password`, `password`, `role`, `college`, `created_at`) VALUES
(1, 'Ram Sharma', 'ram@gmail.com', '9812345678', 'pass123', '9b8769a4a742959a2d0298c36fb70623f2dfacda8436237df08d8dfd5b37374c', 'student', NULL, '2026-07-12 12:08:54'),
(2, 'Admin User', 'admin@complainify.edu', '9800000000', 'admin123', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin', NULL, '2026-07-12 12:08:54'),
(3, 'Samir Poudel', 'abc@gmail.com', '9800000006', '#Zayn#123', 'f3c20e807344e89e9cade6e4735ef6acf597942c22eeb4cc666932b98e291ce6', 'student', NULL, '2026-07-17 16:33:31'),
(4, 'Kyle Jenner', 'jenner@gmail.com', '9871234567', '#Zayn#123', 'f3c20e807344e89e9cade6e4735ef6acf597942c22eeb4cc666932b98e291ce6', 'student', NULL, '2026-07-17 16:45:15'),
(5, 'Samirr Poudel', 'cr7samiee@gmail.com', '9800000006', '#Zayn#123', 'f3c20e807344e89e9cade6e4735ef6acf597942c22eeb4cc666932b98e291ce6', 'student', 'College of Engineering', '2026-07-27 15:20:14'),
(6, 'Goli Bar', 'golibar26@gmail.com', '9812345678', '#Zayn#123', 'f3c20e807344e89e9cade6e4735ef6acf597942c22eeb4cc666932b98e291ce6', 'student', 'College of Engineering', '2026-09-27 04:18:34');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `colleges`
--
ALTER TABLE `colleges`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `complaints`
--
ALTER TABLE `complaints`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ticket_id` (`ticket_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `complaint_comments`
--
ALTER TABLE `complaint_comments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `complaint_id` (`complaint_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `otps`
--
ALTER TABLE `otps`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `audit_logs`
--
ALTER TABLE `audit_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=86;

--
-- AUTO_INCREMENT for table `colleges`
--
ALTER TABLE `colleges`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `complaints`
--
ALTER TABLE `complaints`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=41;

--
-- AUTO_INCREMENT for table `complaint_comments`
--
ALTER TABLE `complaint_comments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=48;

--
-- AUTO_INCREMENT for table `otps`
--
ALTER TABLE `otps`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `complaints`
--
ALTER TABLE `complaints`
  ADD CONSTRAINT `complaints_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `complaint_comments`
--
ALTER TABLE `complaint_comments`
  ADD CONSTRAINT `complaint_comments_ibfk_1` FOREIGN KEY (`complaint_id`) REFERENCES `complaints` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `complaint_comments_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
