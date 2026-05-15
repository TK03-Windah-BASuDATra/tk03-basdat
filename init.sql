
-- ==================================================
-- CREATE SCHEMA
-- ==================================================
CREATE SCHEMA IF NOT EXISTS windah_basudatra;

-- pakai schema tersebut
SET search_path TO windah_basudatra;

-- extension tetap global (tidak perlu schema)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

--------------------------------------------------
-- DROP TABLES (reverse dependency order)
--------------------------------------------------

-- DROP TABLE IF EXISTS has_relationship CASCADE;
-- DROP TABLE IF EXISTS ticket CASCADE;
-- DROP TABLE IF EXISTS order_promotion CASCADE;
-- DROP TABLE IF EXISTS promotion CASCADE;
-- DROP TABLE IF EXISTS "order" CASCADE;
-- DROP TABLE IF EXISTS ticket_category CASCADE;
-- DROP TABLE IF EXISTS event_artist CASCADE;
-- DROP TABLE IF EXISTS artist CASCADE;
-- DROP TABLE IF EXISTS event CASCADE;
-- DROP TABLE IF EXISTS seat CASCADE;
-- DROP TABLE IF EXISTS venue CASCADE;
-- DROP TABLE IF EXISTS organizer CASCADE;
-- DROP TABLE IF EXISTS customer CASCADE;
-- DROP TABLE IF EXISTS account_role CASCADE;
-- DROP TABLE IF EXISTS role CASCADE;
-- DROP TABLE IF EXISTS user_account CASCADE;


--------------------------------------------------
-- USER_ACCOUNT
--------------------------------------------------

CREATE TABLE user_account (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);


--------------------------------------------------
-- ROLE
--------------------------------------------------

CREATE TABLE role (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_name VARCHAR(50) UNIQUE NOT NULL
);


--------------------------------------------------
-- ACCOUNT_ROLE
--------------------------------------------------

CREATE TABLE account_role (
    role_id UUID,
    user_id UUID,

    PRIMARY KEY(role_id, user_id),

    FOREIGN KEY(role_id)
        REFERENCES role(role_id)
        ON DELETE CASCADE,

    FOREIGN KEY(user_id)
        REFERENCES user_account(user_id)
        ON DELETE CASCADE
);


--------------------------------------------------
-- CUSTOMER
--------------------------------------------------

CREATE TABLE customer (
    customer_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name    VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    contact_email VARCHAR(100),
    user_id      UUID UNIQUE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user_account(user_id)
);


--------------------------------------------------
-- ORGANIZER
--------------------------------------------------

CREATE TABLE organizer (
    organizer_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organizer_name VARCHAR(100) NOT NULL,
    contact_email  VARCHAR(100),
    phone_number   VARCHAR(20),
    user_id        UUID UNIQUE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user_account(user_id)
);



--------------------------------------------------
-- VENUE
--------------------------------------------------

CREATE TABLE venue (
    venue_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    venue_name    VARCHAR(100) NOT NULL,
    capacity      INTEGER NOT NULL CHECK(capacity > 0),
    address       TEXT NOT NULL,
    city          VARCHAR(100) NOT NULL,
    tipe_seating  VARCHAR(20) NOT NULL
        CHECK(tipe_seating IN ('FREE_SEATING', 'RESERVED_SEATING'))
);

--------------------------------------------------
-- SEAT
--------------------------------------------------

CREATE TABLE seat (
    seat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section VARCHAR(50) NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    row_number VARCHAR(10) NOT NULL,

    venue_id UUID NOT NULL,

    FOREIGN KEY(venue_id)
        REFERENCES venue(venue_id),

    UNIQUE(venue_id,row_number,seat_number)
);


--------------------------------------------------
-- EVENT
--------------------------------------------------

CREATE TABLE event (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_datetime TIMESTAMP NOT NULL,
    event_title VARCHAR(200) NOT NULL,

    venue_id UUID NOT NULL,
    organizer_id UUID NOT NULL,

    FOREIGN KEY(venue_id)
        REFERENCES venue(venue_id),

    FOREIGN KEY(organizer_id)
        REFERENCES organizer(organizer_id)
);


--------------------------------------------------
-- ARTIST
--------------------------------------------------

CREATE TABLE artist (
    artist_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    genre VARCHAR(100)
);


--------------------------------------------------
-- EVENT_ARTIST
--------------------------------------------------

CREATE TABLE event_artist (
    event_id UUID,
    artist_id UUID,
    role VARCHAR(100),

    PRIMARY KEY(event_id, artist_id),

    FOREIGN KEY(event_id)
        REFERENCES event(event_id),

    FOREIGN KEY(artist_id)
        REFERENCES artist(artist_id)
);


--------------------------------------------------
-- TICKET_CATEGORY
--------------------------------------------------

CREATE TABLE ticket_category (
    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_name VARCHAR(50) NOT NULL,
    quota INTEGER NOT NULL CHECK(quota > 0),
    price NUMERIC(12,2) NOT NULL CHECK(price >=0),

    event_id UUID NOT NULL,

    FOREIGN KEY(event_id)
        REFERENCES event(event_id)
);


--------------------------------------------------
-- "ORDER"
--------------------------------------------------

CREATE TABLE "order" (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_date TIMESTAMP NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL CHECK(total_amount>=0),

    customer_id UUID NOT NULL,

    FOREIGN KEY(customer_id)
        REFERENCES customer(customer_id)
);


--------------------------------------------------
-- PROMOTION
--------------------------------------------------

CREATE TABLE promotion (
    promotion_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    promo_code VARCHAR(50) UNIQUE NOT NULL,

    discount_type VARCHAR(20) NOT NULL
        CHECK(
            discount_type IN
            ('NOMINAL','PERCENTAGE')
        ),

    discount_value NUMERIC(12,2)
        NOT NULL CHECK(discount_value >0),

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    usage_limit INTEGER
        NOT NULL CHECK(usage_limit>0)
);


--------------------------------------------------
-- ORDER_PROMOTION
--------------------------------------------------

CREATE TABLE order_promotion (
    order_promotion_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    promotion_id UUID NOT NULL,
    order_id UUID NOT NULL,

    FOREIGN KEY(promotion_id)
        REFERENCES promotion(promotion_id),

    FOREIGN KEY(order_id)
        REFERENCES "order"(order_id)
);


--------------------------------------------------
-- TICKET
--------------------------------------------------

CREATE TABLE ticket (
    ticket_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    ticket_code VARCHAR(100)
        UNIQUE NOT NULL,

    category_id UUID NOT NULL,
    order_id UUID NOT NULL,

    FOREIGN KEY(category_id)
        REFERENCES ticket_category(category_id),

    FOREIGN KEY(order_id)
        REFERENCES "order"(order_id)
);


--------------------------------------------------
-- HAS_RELATIONSHIP
--------------------------------------------------

CREATE TABLE has_relationship (
    seat_id UUID,
    ticket_id UUID,

    PRIMARY KEY(seat_id,ticket_id),

    FOREIGN KEY(seat_id)
        REFERENCES seat(seat_id),

    FOREIGN KEY(ticket_id)
        REFERENCES ticket(ticket_id)
);





--------------------------------------------------
-- ============================================ --
-- ================ DUMMY DATA ================ --
-- ============================================ --
--------------------------------------------------

-- ============================================================
-- DUMMY DATA - Basis Data CSGE602070
-- TA 2025/2026 - Semester Genap
-- ============================================================

-- ============================================================
-- 1. USER_ACCOUNT (12 rows)
-- ============================================================
INSERT INTO user_account (user_id, username, password) VALUES
	('00000000-0000-0000-0000-000000000001', 'alicesmith',    'hashed_pw_001'),
('00000000-0000-0000-0000-000000000002', 'bobones',      'hashed_pw_002'),
('00000000-0000-0000-0000-000000000003', 'carolwhite',    'hashed_pw_003'),
('00000000-0000-0000-0000-000000000004', 'davebrown',     'hashed_pw_004'),
('00000000-0000-0000-0000-000000000005', 'evedavis',      'hashed_pw_005'),
('00000000-0000-0000-0000-000000000006', 'frankmiller',   'hashed_pw_006'),
('00000000-0000-0000-0000-000000000007', 'orgsoundwave',  'hashed_pw_007'),
('00000000-0000-0000-0000-000000000008', 'orgstagelive',  'hashed_pw_008'),
('00000000-0000-0000-0000-000000000009', 'orgnightfest',  'hashed_pw_009'),
('00000000-0000-0000-0000-000000000010', 'orgeventpro',   'hashed_pw_010'),
('00000000-0000-0000-0000-000000000011', 'gracelee',      'hashed_pw_011'),
('00000000-0000-0000-0000-000000000012', 'henrytan',      'hashed_pw_012');


-- ============================================================
-- 2. ROLE (3 rows)
-- ============================================================
INSERT INTO role (role_id, role_name) VALUES
('10000000-0000-0000-0000-000000000001', 'ADMIN'),
('10000000-0000-0000-0000-000000000002', 'CUSTOMER'),
('10000000-0000-0000-0000-000000000003', 'ORGANIZER');


-- ============================================================
-- 3. ACCOUNT_ROLE (15 rows)
-- ============================================================
INSERT INTO account_role (role_id, user_id) VALUES
-- 6 customers get CUSTOMER role
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000004'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000005'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000006'),
-- 4 organizers get ORGANIZER role
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000007'),
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000008'),
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000009'),
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000010'),
-- remaining users get ADMIN role
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011'),
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000012'),
-- some users have multiple roles
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000011'),
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000012');


-- ============================================================
-- 4. CUSTOMER (6 rows)
-- ============================================================
INSERT INTO customer (customer_id, full_name, phone_number, contact_email, user_id) VALUES
('20000000-0000-0000-0000-000000000001', 'Alice Smith',  '081234567890', 'alice@example.com',  '00000000-0000-0000-0000-000000000001'),
('20000000-0000-0000-0000-000000000002', 'Bob Jones',    '082345678901', 'bob@example.com',    '00000000-0000-0000-0000-000000000002'),
('20000000-0000-0000-0000-000000000003', 'Carol White',  '083456789012', 'carol@example.com',  '00000000-0000-0000-0000-000000000003'),
('20000000-0000-0000-0000-000000000004', 'Dave Brown',   '084567890123', 'dave@example.com',   '00000000-0000-0000-0000-000000000004'),
('20000000-0000-0000-0000-000000000005', 'Eve Davis',    '085678901234', 'eve@example.com',    '00000000-0000-0000-0000-000000000005'),
('20000000-0000-0000-0000-000000000006', 'Frank Miller', '086789012345', 'frank@example.com',  '00000000-0000-0000-0000-000000000006');


-- ============================================================
-- 5. ORGANIZER (4 rows)
-- ============================================================
INSERT INTO organizer (organizer_id, organizer_name, contact_email, phone_number, user_id) VALUES
('30000000-0000-0000-0000-000000000001', 'Soundwave Events', 'contact@soundwave.id', '02111111111', '00000000-0000-0000-0000-000000000007'),
('30000000-0000-0000-0000-000000000002', 'Stage Live Co.',   'info@stagelive.id',    '02122222222', '00000000-0000-0000-0000-000000000008'),
('30000000-0000-0000-0000-000000000003', 'Night Fest Org',   'hello@nightfest.id',   '02133333333', '00000000-0000-0000-0000-000000000009'),
('30000000-0000-0000-0000-000000000004', 'EventPro Jakarta', 'support@eventpro.id',  '02144444444', '00000000-0000-0000-0000-000000000010');


-- ============================================================
-- 6. VENUE (5 rows)
-- ============================================================
INSERT INTO venue (venue_id, venue_name, capacity, address, city, tipe_seating) VALUES
('40000000-0000-0000-0000-000000000001', 'Jakarta Convention Center', 5000, 'Jl. Gatot Subroto, Senayan',      'Jakarta', 'RESERVED_SEATING'),
('40000000-0000-0000-0000-000000000002', 'Istora Senayan',            4000, 'Jl. Pintu Satu Senayan',           'Jakarta', 'RESERVED_SEATING'),
('40000000-0000-0000-0000-000000000003', 'Gelora Bung Karno Hall',    8000, 'Jl. Pintu X-XI Senayan',           'Jakarta', 'FREE_SEATING'),
('40000000-0000-0000-0000-000000000004', 'Balai Sarbini',             1500, 'Jl. Jend. Sudirman Kav. 1',        'Jakarta', 'RESERVED_SEATING'),
('40000000-0000-0000-0000-000000000005', 'Tennis Indoor Senayan',     3000, 'Jl. Asia Afrika Pintu IX Senayan', 'Jakarta', 'FREE_SEATING');

-- ============================================================
-- 7. SEAT (30 rows) — 6 seats per venue
-- ============================================================
INSERT INTO seat (seat_id, section, seat_number, row_number, venue_id) VALUES
-- Venue 1
('50000000-0000-0000-0000-000000000001', 'VIP',     'S001', 'A', '40000000-0000-0000-0000-000000000001'),
('50000000-0000-0000-0000-000000000002', 'VIP',     'S002', 'A', '40000000-0000-0000-0000-000000000001'),
('50000000-0000-0000-0000-000000000003', 'Regular', 'S001', 'B', '40000000-0000-0000-0000-000000000001'),
('50000000-0000-0000-0000-000000000004', 'Regular', 'S002', 'B', '40000000-0000-0000-0000-000000000001'),
('50000000-0000-0000-0000-000000000005', 'VVIP',    'S001', 'C', '40000000-0000-0000-0000-000000000001'),
('50000000-0000-0000-0000-000000000006', 'VVIP',    'S002', 'C', '40000000-0000-0000-0000-000000000001'),
-- Venue 2
('50000000-0000-0000-0000-000000000007', 'VIP',     'S001', 'A', '40000000-0000-0000-0000-000000000002'),
('50000000-0000-0000-0000-000000000008', 'VIP',     'S002', 'A', '40000000-0000-0000-0000-000000000002'),
('50000000-0000-0000-0000-000000000009', 'Regular', 'S001', 'B', '40000000-0000-0000-0000-000000000002'),
('50000000-0000-0000-0000-000000000010', 'Regular', 'S002', 'B', '40000000-0000-0000-0000-000000000002'),
('50000000-0000-0000-0000-000000000011', 'VVIP',    'S001', 'C', '40000000-0000-0000-0000-000000000002'),
('50000000-0000-0000-0000-000000000012', 'VVIP',    'S002', 'C', '40000000-0000-0000-0000-000000000002'),
-- Venue 3
('50000000-0000-0000-0000-000000000013', 'VIP',     'S001', 'A', '40000000-0000-0000-0000-000000000003'),
('50000000-0000-0000-0000-000000000014', 'VIP',     'S002', 'A', '40000000-0000-0000-0000-000000000003'),
('50000000-0000-0000-0000-000000000015', 'Regular', 'S001', 'B', '40000000-0000-0000-0000-000000000003'),
('50000000-0000-0000-0000-000000000016', 'Regular', 'S002', 'B', '40000000-0000-0000-0000-000000000003'),
('50000000-0000-0000-0000-000000000017', 'VVIP',    'S001', 'C', '40000000-0000-0000-0000-000000000003'),
('50000000-0000-0000-0000-000000000018', 'VVIP',    'S002', 'C', '40000000-0000-0000-0000-000000000003'),
-- Venue 4
('50000000-0000-0000-0000-000000000019', 'VIP',     'S001', 'A', '40000000-0000-0000-0000-000000000004'),
('50000000-0000-0000-0000-000000000020', 'VIP',     'S002', 'A', '40000000-0000-0000-0000-000000000004'),
('50000000-0000-0000-0000-000000000021', 'Regular', 'S001', 'B', '40000000-0000-0000-0000-000000000004'),
('50000000-0000-0000-0000-000000000022', 'Regular', 'S002', 'B', '40000000-0000-0000-0000-000000000004'),
('50000000-0000-0000-0000-000000000023', 'VVIP',    'S001', 'C', '40000000-0000-0000-0000-000000000004'),
('50000000-0000-0000-0000-000000000024', 'VVIP',    'S002', 'C', '40000000-0000-0000-0000-000000000004'),
-- Venue 5
('50000000-0000-0000-0000-000000000025', 'VIP',     'S001', 'A', '40000000-0000-0000-0000-000000000005'),
('50000000-0000-0000-0000-000000000026', 'VIP',     'S002', 'A', '40000000-0000-0000-0000-000000000005'),
('50000000-0000-0000-0000-000000000027', 'Regular', 'S001', 'B', '40000000-0000-0000-0000-000000000005'),
('50000000-0000-0000-0000-000000000028', 'Regular', 'S002', 'B', '40000000-0000-0000-0000-000000000005'),
('50000000-0000-0000-0000-000000000029', 'VVIP',    'S001', 'C', '40000000-0000-0000-0000-000000000005'),
('50000000-0000-0000-0000-000000000030', 'VVIP',    'S002', 'C', '40000000-0000-0000-0000-000000000005');


-- ============================================================
-- 8. ARTIST (8 rows)
-- ============================================================
INSERT INTO artist (artist_id, name, genre) VALUES
('60000000-0000-0000-0000-000000000001', 'Raisa',           'Pop'),
('60000000-0000-0000-0000-000000000002', 'Tulus',            'Pop'),
('60000000-0000-0000-0000-000000000003', 'Noah Band',        'Rock'),
('60000000-0000-0000-0000-000000000004', 'Isyana Sarasvati', 'Pop'),
('60000000-0000-0000-0000-000000000005', 'Sheila on 7',      'Pop Rock'),
('60000000-0000-0000-0000-000000000006', 'Dewa 19',          'Rock'),
('60000000-0000-0000-0000-000000000007', 'Rizky Febian',     'R&B'),
('60000000-0000-0000-0000-000000000008', 'Hindia',           'Indie');


-- ============================================================
-- 9. EVENT (9 rows) — 3 past, 6 upcoming
-- ============================================================
INSERT INTO event (event_id, event_datetime, event_title, venue_id, organizer_id) VALUES
('70000000-0000-0000-0000-000000000001', '2026-02-14 19:00:00'::timestamp, 'Raisa Live in Concert',        '40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001'),
('70000000-0000-0000-0000-000000000002', '2026-03-08 18:00:00'::timestamp, 'Tulus - Tur Manusia',          '40000000-0000-0000-0000-000000000002', '30000000-0000-0000-0000-000000000001'),
('70000000-0000-0000-0000-000000000003', '2026-04-19 20:00:00'::timestamp, 'Jakarta Music Festival 2026',  '40000000-0000-0000-0000-000000000003', '30000000-0000-0000-0000-000000000002'),
('70000000-0000-0000-0000-000000000004', '2026-05-10 19:30:00'::timestamp, 'Night Fest - Rock Edition',    '40000000-0000-0000-0000-000000000004', '30000000-0000-0000-0000-000000000003'),
('70000000-0000-0000-0000-000000000005', '2026-06-07 17:00:00'::timestamp, 'Year End Spectacular',         '40000000-0000-0000-0000-000000000005', '30000000-0000-0000-0000-000000000004'),
('70000000-0000-0000-0000-000000000006', '2026-07-05 19:00:00'::timestamp, 'New Year Indie Bash',          '40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000002'),
('70000000-0000-0000-0000-000000000007', '2026-08-15 20:00:00'::timestamp, 'Sheila on Seven - Tunggu Aku', '40000000-0000-0000-0000-000000000002', '30000000-0000-0000-0000-000000000003'),
('70000000-0000-0000-0000-000000000008', '2026-09-12 18:30:00'::timestamp, 'Dewa 19 Reunion Tour',         '40000000-0000-0000-0000-000000000003', '30000000-0000-0000-0000-000000000004'),
('70000000-0000-0000-0000-000000000009', '2026-10-24 19:00:00'::timestamp, 'Hindia - Menari Dalam Badai',  '40000000-0000-0000-0000-000000000005', '30000000-0000-0000-0000-000000000001');



-- ============================================================
-- 10. EVENT_ARTIST (12 rows)
-- ============================================================
INSERT INTO event_artist (event_id, artist_id, role) VALUES
('70000000-0000-0000-0000-000000000001', '60000000-0000-0000-0000-000000000001', 'Headliner'),
('70000000-0000-0000-0000-000000000001', '60000000-0000-0000-0000-000000000007', 'Opening Act'),
('70000000-0000-0000-0000-000000000002', '60000000-0000-0000-0000-000000000002', 'Headliner'),
('70000000-0000-0000-0000-000000000002', '60000000-0000-0000-0000-000000000004', 'Guest Star'),
('70000000-0000-0000-0000-000000000003', '60000000-0000-0000-0000-000000000003', 'Headliner'),
('70000000-0000-0000-0000-000000000003', '60000000-0000-0000-0000-000000000005', 'Co-Headliner'),
('70000000-0000-0000-0000-000000000003', '60000000-0000-0000-0000-000000000008', 'Opening Act'),
('70000000-0000-0000-0000-000000000004', '60000000-0000-0000-0000-000000000006', 'Headliner'),
('70000000-0000-0000-0000-000000000004', '60000000-0000-0000-0000-000000000003', 'Co-Headliner'),
('70000000-0000-0000-0000-000000000005', '60000000-0000-0000-0000-000000000001', 'Guest Star'),
('70000000-0000-0000-0000-000000000005', '60000000-0000-0000-0000-000000000002', 'Guest Star'),
('70000000-0000-0000-0000-000000000006', '60000000-0000-0000-0000-000000000008', 'Headliner');


-- ============================================================
-- 11. TICKET_CATEGORY
-- ============================================================
INSERT INTO ticket_category (category_id, category_name, quota, price, event_id) VALUES
('80000000-0000-0000-0000-000000000001', 'VVIP',     50,  2500000.00, '70000000-0000-0000-0000-000000000001'),
('80000000-0000-0000-0000-000000000002', 'VIP',     150,  1500000.00, '70000000-0000-0000-0000-000000000001'),
('80000000-0000-0000-0000-000000000003', 'Regular', 500,   500000.00, '70000000-0000-0000-0000-000000000001'),
('80000000-0000-0000-0000-000000000004', 'VVIP',     40,  2000000.00, '70000000-0000-0000-0000-000000000002'),
('80000000-0000-0000-0000-000000000005', 'VIP',     100,  1200000.00, '70000000-0000-0000-0000-000000000002'),
('80000000-0000-0000-0000-000000000006', 'Regular', 400,   400000.00, '70000000-0000-0000-0000-000000000002'),
('80000000-0000-0000-0000-000000000007', 'VVIP',     60,  3000000.00, '70000000-0000-0000-0000-000000000003'),
('80000000-0000-0000-0000-000000000008', 'VIP',     200,  1800000.00, '70000000-0000-0000-0000-000000000003'),
('80000000-0000-0000-0000-000000000009', 'VIP',     100,  1000000.00, '70000000-0000-0000-0000-000000000004'),
('80000000-0000-0000-0000-000000000010', 'Regular', 300,   350000.00, '70000000-0000-0000-0000-000000000004'),
('80000000-0000-0000-0000-000000000011', 'VVIP',     30,  3500000.00, '70000000-0000-0000-0000-000000000005'),
('80000000-0000-0000-0000-000000000012', 'VIP',     120,  2000000.00, '70000000-0000-0000-0000-000000000005'),
('80000000-0000-0000-0000-000000000013', 'VIP',      80,   800000.00, '70000000-0000-0000-0000-000000000006'),
('80000000-0000-0000-0000-000000000014', 'Regular', 250,   250000.00, '70000000-0000-0000-0000-000000000006'),
('80000000-0000-0000-0000-000000000015', 'VVIP',    50,  2200000.00, '70000000-0000-0000-0000-000000000007'),
('80000000-0000-0000-0000-000000000016', 'VIP',    150,  1300000.00, '70000000-0000-0000-0000-000000000007'),
('80000000-0000-0000-0000-000000000017', 'Regular',400,   450000.00, '70000000-0000-0000-0000-000000000007'),
('80000000-0000-0000-0000-000000000018', 'VVIP',    40,  3000000.00, '70000000-0000-0000-0000-000000000008'),
('80000000-0000-0000-0000-000000000019', 'VIP',    200,  1800000.00, '70000000-0000-0000-0000-000000000008'),
('80000000-0000-0000-0000-000000000020', 'Regular',500,   600000.00, '70000000-0000-0000-0000-000000000008'),
('80000000-0000-0000-0000-000000000021', 'VIP',    100,   900000.00, '70000000-0000-0000-0000-000000000009'),
('80000000-0000-0000-0000-000000000022', 'Regular',300,   350000.00, '70000000-0000-0000-0000-000000000009');



-- ============================================================
-- 12. PROMOTION (9 rows) — 3 past, 6 active
-- ============================================================
INSERT INTO promotion (promotion_id, promo_code, discount_type, discount_value, start_date, end_date, usage_limit) VALUES
-- PAST (expired)
('90000000-0000-0000-0000-000000000001', 'VALENTINE10',   'PERCENTAGE', 10.00,    '2026-02-01', '2026-02-28', 100),
('90000000-0000-0000-0000-000000000002', 'MARET50K',      'NOMINAL',    50000.00, '2026-03-01', '2026-03-31', 200),
('90000000-0000-0000-0000-000000000003', 'APRIL15',       'PERCENTAGE', 15.00,    '2026-04-01', '2026-04-30',  50),
-- ACTIVE / UPCOMING
('90000000-0000-0000-0000-000000000004', 'MEI25K',        'NOMINAL',    25000.00, '2026-05-01', '2026-05-31', 150),
('90000000-0000-0000-0000-000000000005', 'EARLYBIRD20',   'PERCENTAGE', 20.00,    '2026-05-01', '2026-06-30',  75),
('90000000-0000-0000-0000-000000000006', 'SAVE100K',      'NOMINAL',   100000.00, '2026-05-15', '2026-07-15',  60),
('90000000-0000-0000-0000-000000000007', 'FESTPRO15',     'PERCENTAGE', 15.00,    '2026-06-01', '2026-08-31',  80),
('90000000-0000-0000-0000-000000000008', 'AGUSTUS75K',    'NOMINAL',    75000.00, '2026-07-01', '2026-09-30', 120),
('90000000-0000-0000-0000-000000000009', 'YEARENDSALE25', 'PERCENTAGE', 25.00,    '2026-09-01', '2026-10-31',  40);


-- ============================================================
-- 13. ORDER (16 rows) — mix status, semua order_date di masa lalu
-- ============================================================
INSERT INTO "order" (order_id, order_date, payment_status, total_amount, customer_id) VALUES
('A0000000-0000-0000-0000-000000000001', '2026-02-15 10:00:00', 'PAID',    1500000.00, '20000000-0000-0000-0000-000000000001'),
('A0000000-0000-0000-0000-000000000002', '2026-02-16 11:30:00', 'PAID',     500000.00, '20000000-0000-0000-0000-000000000002'),
('A0000000-0000-0000-0000-000000000003', '2026-03-09 09:00:00', 'PENDING',  400000.00, '20000000-0000-0000-0000-000000000003'),
('A0000000-0000-0000-0000-000000000004', '2026-03-10 14:00:00', 'PAID',    2000000.00, '20000000-0000-0000-0000-000000000004'),
('A0000000-0000-0000-0000-000000000005', '2026-03-20 08:45:00', 'PAID',    1200000.00, '20000000-0000-0000-0000-000000000005'),
('A0000000-0000-0000-0000-000000000006', '2026-04-01 16:20:00', 'FAILED',   350000.00, '20000000-0000-0000-0000-000000000006'),
('A0000000-0000-0000-0000-000000000007', '2026-04-05 13:00:00', 'PAID',    3000000.00, '20000000-0000-0000-0000-000000000001'),
('A0000000-0000-0000-0000-000000000008', '2026-04-10 10:10:00', 'PAID',    1800000.00, '20000000-0000-0000-0000-000000000002'),
('A0000000-0000-0000-0000-000000000009', '2026-04-15 07:30:00', 'PENDING', 1000000.00, '20000000-0000-0000-0000-000000000003'),
('A0000000-0000-0000-0000-000000000010', '2026-04-18 19:00:00', 'PAID',    3500000.00, '20000000-0000-0000-0000-000000000004'),
('A0000000-0000-0000-0000-000000000011', '2026-04-20 12:00:00', 'PAID',    2000000.00, '20000000-0000-0000-0000-000000000005'),
('A0000000-0000-0000-0000-000000000012', '2026-04-22 15:30:00', 'PAID',     800000.00, '20000000-0000-0000-0000-000000000006'),
('A0000000-0000-0000-0000-000000000013', '2026-04-25 09:00:00', 'FAILED',   450000.00, '20000000-0000-0000-0000-000000000001'),
('A0000000-0000-0000-0000-000000000014', '2026-04-27 14:00:00', 'PAID',    1300000.00, '20000000-0000-0000-0000-000000000002'),
('A0000000-0000-0000-0000-000000000015', '2026-04-29 11:00:00', 'PENDING',  900000.00, '20000000-0000-0000-0000-000000000004'),
('A0000000-0000-0000-0000-000000000016', '2026-05-01 17:45:00', 'PAID',    2200000.00, '20000000-0000-0000-0000-000000000005');


-- ============================================================
-- 14. ORDER_PROMOTION (5 rows)
-- ============================================================
INSERT INTO order_promotion (order_promotion_id, promotion_id, order_id) VALUES
('B0000000-0000-0000-0000-000000000001', '90000000-0000-0000-0000-000000000001', 'A0000000-0000-0000-0000-000000000001'),
('B0000000-0000-0000-0000-000000000002', '90000000-0000-0000-0000-000000000002', 'A0000000-0000-0000-0000-000000000002'),
('B0000000-0000-0000-0000-000000000003', '90000000-0000-0000-0000-000000000003', 'A0000000-0000-0000-0000-000000000007'),
('B0000000-0000-0000-0000-000000000004', '90000000-0000-0000-0000-000000000005', 'A0000000-0000-0000-0000-000000000010'),
('B0000000-0000-0000-0000-000000000005', '90000000-0000-0000-0000-000000000006', 'A0000000-0000-0000-0000-000000000012');


-- ============================================================
-- 15. TICKET (20 rows)
-- ============================================================
INSERT INTO ticket (ticket_id, ticket_code, category_id, order_id) VALUES
('C0000000-0000-0000-0000-000000000001', 'TKT-2025-0001', '80000000-0000-0000-0000-000000000002', 'A0000000-0000-0000-0000-000000000001'),
('C0000000-0000-0000-0000-000000000002', 'TKT-2025-0002', '80000000-0000-0000-0000-000000000003', 'A0000000-0000-0000-0000-000000000002'),
('C0000000-0000-0000-0000-000000000003', 'TKT-2025-0003', '80000000-0000-0000-0000-000000000006', 'A0000000-0000-0000-0000-000000000003'),
('C0000000-0000-0000-0000-000000000004', 'TKT-2025-0004', '80000000-0000-0000-0000-000000000004', 'A0000000-0000-0000-0000-000000000004'),
('C0000000-0000-0000-0000-000000000005', 'TKT-2025-0005', '80000000-0000-0000-0000-000000000005', 'A0000000-0000-0000-0000-000000000005'),
('C0000000-0000-0000-0000-000000000006', 'TKT-2025-0006', '80000000-0000-0000-0000-000000000010', 'A0000000-0000-0000-0000-000000000006'),
('C0000000-0000-0000-0000-000000000007', 'TKT-2025-0007', '80000000-0000-0000-0000-000000000007', 'A0000000-0000-0000-0000-000000000007'),
('C0000000-0000-0000-0000-000000000008', 'TKT-2025-0008', '80000000-0000-0000-0000-000000000008', 'A0000000-0000-0000-0000-000000000008'),
('C0000000-0000-0000-0000-000000000009', 'TKT-2025-0009', '80000000-0000-0000-0000-000000000009', 'A0000000-0000-0000-0000-000000000009'),
('C0000000-0000-0000-0000-000000000010', 'TKT-2025-0010', '80000000-0000-0000-0000-000000000011', 'A0000000-0000-0000-0000-000000000010'),
('C0000000-0000-0000-0000-000000000011', 'TKT-2025-0011', '80000000-0000-0000-0000-000000000012', 'A0000000-0000-0000-0000-000000000011'),
('C0000000-0000-0000-0000-000000000012', 'TKT-2025-0012', '80000000-0000-0000-0000-000000000013', 'A0000000-0000-0000-0000-000000000012'),
('C0000000-0000-0000-0000-000000000013', 'TKT-2025-0013', '80000000-0000-0000-0000-000000000001', 'A0000000-0000-0000-0000-000000000001'),
('C0000000-0000-0000-0000-000000000014', 'TKT-2025-0014', '80000000-0000-0000-0000-000000000003', 'A0000000-0000-0000-0000-000000000002'),
('C0000000-0000-0000-0000-000000000015', 'TKT-2025-0015', '80000000-0000-0000-0000-000000000005', 'A0000000-0000-0000-0000-000000000004'),
('C0000000-0000-0000-0000-000000000016', 'TKT-2025-0016', '80000000-0000-0000-0000-000000000008', 'A0000000-0000-0000-0000-000000000007'),
('C0000000-0000-0000-0000-000000000017', 'TKT-2025-0017', '80000000-0000-0000-0000-000000000010', 'A0000000-0000-0000-0000-000000000009'),
('C0000000-0000-0000-0000-000000000018', 'TKT-2025-0018', '80000000-0000-0000-0000-000000000012', 'A0000000-0000-0000-0000-000000000010'),
('C0000000-0000-0000-0000-000000000019', 'TKT-2025-0019', '80000000-0000-0000-0000-000000000014', 'A0000000-0000-0000-0000-000000000011'),
('C0000000-0000-0000-0000-000000000020', 'TKT-2025-0020', '80000000-0000-0000-0000-000000000014', 'A0000000-0000-0000-0000-000000000012');


-- ============================================================
-- 16. HAS_RELATIONSHIP (10 rows)
-- ============================================================
INSERT INTO has_relationship (seat_id, ticket_id) VALUES
('50000000-0000-0000-0000-000000000001', 'C0000000-0000-0000-0000-000000000001'),
('50000000-0000-0000-0000-000000000002', 'C0000000-0000-0000-0000-000000000013'),
('50000000-0000-0000-0000-000000000003', 'C0000000-0000-0000-0000-000000000002'),
('50000000-0000-0000-0000-000000000004', 'C0000000-0000-0000-0000-000000000014'),
('50000000-0000-0000-0000-000000000007', 'C0000000-0000-0000-0000-000000000004'),
('50000000-0000-0000-0000-000000000008', 'C0000000-0000-0000-0000-000000000015'),
('50000000-0000-0000-0000-000000000009', 'C0000000-0000-0000-0000-000000000003'),
('50000000-0000-0000-0000-000000000013', 'C0000000-0000-0000-0000-000000000007'),
('50000000-0000-0000-0000-000000000014', 'C0000000-0000-0000-0000-000000000016'),
('50000000-0000-0000-0000-000000000019', 'C0000000-0000-0000-0000-000000000009');


-- ============================================================
-- TRIGGER 1
-- ============================================================

-- ================================================
-- 1. Cek username case-insensitive
-- 2. Cek username hanya boleh huruf & angka
-- ================================================

-- Fungsi helper (dipanggil Django DAN trigger)
CREATE OR REPLACE FUNCTION windah_basudatra.validate_username(
    p_username VARCHAR,
    p_exclude_id UUID
)
RETURNS void AS $$
BEGIN
    IF p_username !~ '^[a-zA-Z0-9]+$' THEN
        RAISE EXCEPTION 'Username "%" hanya boleh mengandung huruf dan angka tanpa simbol atau spasi.', p_username;
    END IF;

    IF EXISTS (
        SELECT 1 FROM windah_basudatra.user_account
        WHERE LOWER(username) = LOWER(p_username)
          AND (p_exclude_id IS NULL OR user_id <> p_exclude_id)
    ) THEN
        RAISE EXCEPTION 'Username "%" sudah terdaftar, gunakan username lain.', p_username;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Fungsi trigger (wrapper, no args, returns TRIGGER)
CREATE OR REPLACE FUNCTION windah_basudatra.trg_validate_username()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM windah_basudatra.validate_username(NEW.username, NEW.user_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Pasang trigger
DROP TRIGGER IF EXISTS trg_check_username ON windah_basudatra.user_account;
CREATE TRIGGER trg_check_username
BEFORE INSERT OR UPDATE ON windah_basudatra.user_account
FOR EACH ROW EXECUTE FUNCTION windah_basudatra.trg_validate_username();


-- ============================================================
-- TRIGGER 2
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) Trigger: mencegah duplikasi nama venue dalam kota yang sama (ignore case)
CREATE OR REPLACE FUNCTION trg_validate_unique_venue_name_city()
RETURNS trigger AS $$
DECLARE
    existing_id uuid;
BEGIN
    SELECT v.venue_id
    INTO existing_id
    FROM venue v
    WHERE LOWER(v.venue_name) = LOWER(NEW.venue_name)
      AND LOWER(v.city) = LOWER(NEW.city)
      AND v.venue_id <> COALESCE(NEW.venue_id, '00000000-0000-0000-0000-000000000000'::uuid)
    LIMIT 1;

    IF existing_id IS NOT NULL THEN
        RAISE EXCEPTION 'Venue ''%'' di kota ''%'' sudah terdaftar dengan ID %.',
            NEW.venue_name, NEW.city, existing_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS validate_unique_venue_name_city ON venue;
CREATE TRIGGER validate_unique_venue_name_city
BEFORE INSERT OR UPDATE OF venue_name, city ON venue
FOR EACH ROW
EXECUTE FUNCTION trg_validate_unique_venue_name_city();

-- 2) Trigger: mencegah venue dihapus apabila masih memiliki event aktif/akan datang
CREATE OR REPLACE FUNCTION trg_prevent_delete_venue_with_active_event()
RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM event e
        WHERE e.venue_id = OLD.venue_id
          AND e.event_datetime >= NOW()
    ) THEN
        RAISE EXCEPTION 'Venue ''%'' masih memiliki event aktif sehingga tidak dapat dihapus.',
            OLD.venue_name;
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prevent_delete_venue_with_active_event ON venue;
CREATE TRIGGER prevent_delete_venue_with_active_event
BEFORE DELETE ON venue
FOR EACH ROW
EXECUTE FUNCTION trg_prevent_delete_venue_with_active_event();

-- 3) Stored function opsional untuk CUD Venue.
-- Backend boleh memanggil function ini supaya operasi tulis tetap melalui SQL/PostgreSQL.
CREATE OR REPLACE FUNCTION sp_create_venue(
    p_venue_name varchar,
    p_capacity integer,
    p_address text,
    p_city varchar
)
RETURNS uuid AS $$
DECLARE
    new_id uuid;
BEGIN
    INSERT INTO venue (venue_id, venue_name, capacity, address, city)
    VALUES (gen_random_uuid(), p_venue_name, p_capacity, p_address, p_city)
    RETURNING venue_id INTO new_id;

    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_update_venue(
    p_venue_id uuid,
    p_venue_name varchar,
    p_capacity integer,
    p_address text,
    p_city varchar
)
RETURNS void AS $$
BEGIN
    UPDATE venue
    SET venue_name = p_venue_name,
        capacity = p_capacity,
        address = p_address,
        city = p_city
    WHERE venue_id = p_venue_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Venue dengan ID % tidak ditemukan.', p_venue_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sp_delete_venue(p_venue_id uuid)
RETURNS void AS $$
BEGIN
    DELETE FROM venue
    WHERE venue_id = p_venue_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Venue dengan ID % tidak ditemukan.', p_venue_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- TRIGGER 3
-- ============================================================
CREATE OR REPLACE FUNCTION windah_basudatra.validate_event_artist()
RETURNS TRIGGER AS $$
DECLARE
    v_artist_name VARCHAR;
    v_event_title VARCHAR;
BEGIN
    -- Validasi format UUID artist_id
    BEGIN
        PERFORM NEW.artist_id::uuid;
    EXCEPTION WHEN invalid_text_representation THEN
        RAISE EXCEPTION 'ERROR: Artist dengan ID % tidak ditemukan.', NEW.artist_id;
    END;

    -- Validasi format UUID event_id
    BEGIN
        PERFORM NEW.event_id::uuid;
    EXCEPTION WHEN invalid_text_representation THEN
        RAISE EXCEPTION 'ERROR: Event dengan ID % tidak ditemukan.', NEW.event_id;
    END;

    SELECT name INTO v_artist_name
    FROM windah_basudatra.artist
    WHERE artist_id = NEW.artist_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERROR: Artist dengan ID % tidak ditemukan.', NEW.artist_id;
    END IF;

    SELECT event_title INTO v_event_title
    FROM windah_basudatra.event
    WHERE event_id = NEW.event_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERROR: Event dengan ID % tidak ditemukan.', NEW.event_id;
    END IF;

    IF EXISTS (
        SELECT 1 FROM windah_basudatra.event_artist
        WHERE event_id = NEW.event_id AND artist_id = NEW.artist_id
    ) THEN
        RAISE EXCEPTION 'ERROR: Artist "%" sudah terdaftar pada event "%".', v_artist_name, v_event_title;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_validate_event_artist
BEFORE INSERT ON windah_basudatra.event_artist
FOR EACH ROW EXECUTE FUNCTION windah_basudatra.validate_event_artist();


-- Stored Function: Menampilkan sisa kuota ticket category berdasarkan event_id
CREATE OR REPLACE FUNCTION get_ticket_availability(p_event_id TEXT)
RETURNS TABLE (
    category_id UUID,
    category_name VARCHAR,
    price NUMERIC,
    quota INTEGER,
    terjual BIGINT,
    sisa_kuota BIGINT
) AS $$
DECLARE
    v_event_uuid UUID;
BEGIN
    -- Coba cast ke UUID, kalau gagal langsung error sesuai format
    BEGIN
        v_event_uuid := p_event_id::UUID;
    EXCEPTION WHEN invalid_text_representation THEN
        RAISE EXCEPTION 'ERROR: Event dengan ID % tidak ditemukan.', p_event_id;
    END;

    -- Cek event exists
    IF NOT EXISTS (SELECT 1 FROM event WHERE event_id = v_event_uuid) THEN
        RAISE EXCEPTION 'ERROR: Event dengan ID % tidak ditemukan.', p_event_id;
    END IF;

    RETURN QUERY
    SELECT
        tc.category_id,
        tc.category_name,
        tc.price,
        tc.quota,
        COUNT(t.ticket_id) AS terjual,
        tc.quota - COUNT(t.ticket_id) AS sisa_kuota
    FROM ticket_category tc
    LEFT JOIN ticket t ON t.category_id = tc.category_id
    WHERE tc.event_id = v_event_uuid
    GROUP BY tc.category_id, tc.category_name, tc.price, tc.quota
    ORDER BY tc.category_name;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- TRIGGER 4 — Validasi promotion saat digunakan ke order
-- ============================================================
 
SET search_path TO windah_basudatra;
 
CREATE OR REPLACE FUNCTION windah_basudatra.validate_promotion_on_order()
RETURNS TRIGGER AS $$
DECLARE
    v_promo_code    VARCHAR;
    v_usage_limit   INTEGER;
    v_used_count    INTEGER;
    v_event_date    TIMESTAMP;
    v_start_date    DATE;
    v_end_date      DATE;
BEGIN
    SELECT promo_code, usage_limit, start_date, end_date
    INTO v_promo_code, v_usage_limit, v_start_date, v_end_date
    FROM windah_basudatra.promotion
    WHERE promotion_id = NEW.promotion_id;
 
    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERROR: Promotion dengan ID % tidak ditemukan.', NEW.promotion_id;
    END IF;
 
    SELECT COUNT(*) INTO v_used_count
    FROM windah_basudatra.order_promotion
    WHERE promotion_id = NEW.promotion_id;
 
    IF v_used_count >= v_usage_limit THEN
        RAISE EXCEPTION 'ERROR: Promotion "%" telah mencapai batas maksimum penggunaan.', v_promo_code;
    END IF;
 
    SELECT e.event_datetime INTO v_event_date
    FROM windah_basudatra."order" o
    JOIN windah_basudatra.ticket t           ON t.order_id = o.order_id
    JOIN windah_basudatra.ticket_category tc ON tc.category_id = t.category_id
    JOIN windah_basudatra.event e            ON e.event_id = tc.event_id
    WHERE o.order_id = NEW.order_id
    LIMIT 1;
 
    IF v_event_date IS NOT NULL THEN
        IF v_event_date::DATE < v_start_date OR v_event_date::DATE > v_end_date THEN
            RAISE EXCEPTION 'ERROR: Promotion "%" tidak berlaku untuk tanggal event ini.', v_promo_code;
        END IF;
    END IF;
 
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
 
DROP TRIGGER IF EXISTS trg_validate_promotion_on_order
    ON windah_basudatra.order_promotion;
 
CREATE TRIGGER trg_validate_promotion_on_order
    BEFORE INSERT ON windah_basudatra.order_promotion
    FOR EACH ROW
    EXECUTE FUNCTION windah_basudatra.validate_promotion_on_order();

-- ============================================================
-- Dipanggil saat user menekan "Apply Promo" di checkout
-- ============================================================
CREATE OR REPLACE FUNCTION windah_basudatra.validate_promo_for_event(
    p_promo_code VARCHAR,
    p_event_id   TEXT
)
RETURNS TABLE (
    promotion_id   UUID,
    promo_code     VARCHAR,
    discount_type  VARCHAR,
    discount_value NUMERIC
) AS $$
DECLARE
    v_event_uuid   UUID;
    v_promo        RECORD;
    v_used_count   INTEGER;
    v_event_date   DATE;
BEGIN
    -- Cast event_id ke UUID
    BEGIN
        v_event_uuid := p_event_id::UUID;
    EXCEPTION WHEN invalid_text_representation THEN
        RAISE EXCEPTION 'Event dengan ID % tidak ditemukan.', p_event_id;
    END;

    -- Cek event ada
    IF NOT EXISTS (
        SELECT 1 FROM windah_basudatra.event WHERE event_id = v_event_uuid
    ) THEN
        RAISE EXCEPTION 'Event dengan ID % tidak ditemukan.', p_event_id;
    END IF;

    -- Ambil data promo
    SELECT p.promotion_id, p.promo_code, p.discount_type,
           p.discount_value, p.usage_limit, p.start_date, p.end_date
    INTO v_promo
    FROM windah_basudatra.promotion p
    WHERE UPPER(p.promo_code) = UPPER(p_promo_code);

    IF NOT FOUND THEN
        RAISE EXCEPTION 'ERROR: Promotion dengan ID "%" tidak ditemukan.', p_promo_code;
    END IF;

    -- Cek usage limit
    SELECT COUNT(*) INTO v_used_count
    FROM windah_basudatra.order_promotion op
    WHERE op.promotion_id = v_promo.promotion_id;

    IF v_used_count >= v_promo.usage_limit THEN
        RAISE EXCEPTION 'ERROR: Promotion "%" telah mencapai batas maksimum penggunaan.',
            v_promo.promo_code;
    END IF;

    -- Ambil tanggal event
    SELECT e.event_datetime::DATE INTO v_event_date
    FROM windah_basudatra.event e
    WHERE e.event_id = v_event_uuid;

    -- Cek tanggal promo berlaku untuk event ini
    IF v_event_date < v_promo.start_date OR v_event_date > v_promo.end_date THEN
        RAISE EXCEPTION 'ERROR: Promotion "%" tidak berlaku untuk tanggal event ini.',
            v_promo.promo_code;
    END IF;

    -- Semua valid — return data promo
    RETURN QUERY
    SELECT v_promo.promotion_id,
           v_promo.promo_code,
           v_promo.discount_type,
           v_promo.discount_value;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- TRIGGER 5
-- ============================================================
CREATE OR REPLACE FUNCTION check_seat()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT * FROM windah_basudatra.has_relationship WHERE seat_id = OLD.seat_id
    ) THEN
        RAISE EXCEPTION 'ERROR: Kursi % - Baris % No. % tidak dapat dihapus karena sudah terisi.', OLD.section, OLD.row_number, OLD.seat_number;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- DROP TRIGGER IF EXISTS check_seat_before_delete ON windah_basudatra.seat;
CREATE TRIGGER check_seat_before_delete
BEFORE DELETE ON windah_basudatra.seat
FOR EACH ROW EXECUTE FUNCTION check_seat();

CREATE OR REPLACE FUNCTION check_ticket_category_quota()
RETURNS TRIGGER AS $$
DECLARE
    v_quota INT;
    v_used INT;
    v_category_name VARCHAR;
BEGIN
    SELECT quota, category_name INTO v_quota, v_category_name
    FROM windah_basudatra.ticket_category
    WHERE category_id = NEW.category_id;

    SELECT COUNT(*) INTO v_used
    FROM windah_basudatra.ticket
    WHERE category_id = NEW.category_id;

    IF v_used >= v_quota THEN
        RAISE EXCEPTION 'ERROR: Kuota kategori tiket "%" sudah penuh. Tidak dapat membuat tiket baru.', v_category_name;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- DROP TRIGGER IF EXISTS check_ticket_category_quota ON windah_basudatra.ticket;
CREATE TRIGGER check_ticket_category_quota
BEFORE INSERT ON windah_basudatra.ticket
FOR EACH ROW EXECUTE FUNCTION check_ticket_category_quota();


