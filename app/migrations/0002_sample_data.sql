-- splitwise: dev-only
-- Sample data for local development: 4 users, 3 groups with expenses and payments.
-- Safe to run on a database that already has some of these rows. See _docs/tech/guide-migration.md.

INSERT OR IGNORE INTO users (name, created_at) VALUES
  ('Alice', '2026-01-01T09:00:00Z'),
  ('Bob', '2026-01-01T09:00:00Z'),
  ('Carla', '2026-01-01T09:00:00Z'),
  ('Dan', '2026-01-01T09:00:00Z');

-- Codes of the groups that this file creates. Every later row depends on this list.
CREATE TEMP TABLE seed_new (code TEXT PRIMARY KEY);
INSERT INTO seed_new (code) SELECT 'FLA-B2RT'
  WHERE NOT EXISTS (SELECT 1 FROM groups WHERE invite_code = 'FLA-B2RT');
INSERT INTO seed_new (code) SELECT 'TOK-7KQ2'
  WHERE NOT EXISTS (SELECT 1 FROM groups WHERE invite_code = 'TOK-7KQ2');
INSERT INTO seed_new (code) SELECT 'SKI-W3KN'
  WHERE NOT EXISTS (SELECT 1 FROM groups WHERE invite_code = 'SKI-W3KN');

-- Flat 12B (EUR)
INSERT OR IGNORE INTO groups (name, currency, invite_code, created_at)
  VALUES ('Flat 12B', 'EUR', 'FLA-B2RT', '2026-09-01T09:00:00Z');
INSERT INTO members (group_id, user_id, joined_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), (SELECT id FROM users WHERE name = 'Alice'), '2026-09-01T09:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO members (group_id, user_id, joined_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), (SELECT id FROM users WHERE name = 'Bob'), '2026-09-01T09:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO members (group_id, user_id, joined_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), (SELECT id FROM users WHERE name = 'Carla'), '2026-09-01T09:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), 'Rent September', 90000, '2026-09-01', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), '2026-09-01T12:00:00Z', '2026-09-01T12:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Rent September'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 30000 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Rent September'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 30000 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Rent September'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), 30000 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), 'Electricity bill', 10000, '2026-09-10', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), '2026-09-10T12:00:00Z', '2026-09-10T12:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Electricity bill'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 3334 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Electricity bill'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 3333 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Electricity bill'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), 3333 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), 'Internet', 2990, '2026-09-12', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), '2026-09-12T12:00:00Z', '2026-09-12T12:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Internet'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 997 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Internet'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 997 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Internet'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), 996 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), 'Groceries', 5620, '2026-09-20', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), '2026-09-20T12:00:00Z', '2026-09-20T12:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Groceries'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 2810 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Groceries'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 2810 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), 'Rent October', 90000, '2026-10-01', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), '2026-10-01T12:00:00Z', '2026-10-01T12:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Rent October'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 30000 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Rent October'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 30000 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Rent October'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), 30000 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), 'Pizza night', 4551, '2026-10-08', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), '2026-10-08T12:00:00Z', '2026-10-08T12:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Pizza night'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 2276 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND description = 'Pizza night'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 2275 WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO payments (group_id, sender_id, receiver_id, amount, payment_date, note, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 30000, '2026-09-15', 'Rent share, September', '2026-09-15T12:00:00Z', '2026-09-15T12:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);
INSERT INTO payments (group_id, sender_id, receiver_id, amount, payment_date, note, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'FLA-B2RT') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 2000, '2026-10-12', '', '2026-10-12T12:00:00Z', '2026-10-12T12:00:00Z' WHERE 'FLA-B2RT' IN (SELECT code FROM seed_new);

-- Tokyo trip (JPY)
INSERT OR IGNORE INTO groups (name, currency, invite_code, created_at)
  VALUES ('Tokyo trip', 'JPY', 'TOK-7KQ2', '2026-10-05T09:00:00Z');
INSERT INTO members (group_id, user_id, joined_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2'), (SELECT id FROM users WHERE name = 'Alice'), '2026-10-05T09:00:00Z' WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO members (group_id, user_id, joined_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2'), (SELECT id FROM users WHERE name = 'Bob'), '2026-10-05T09:00:00Z' WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO members (group_id, user_id, joined_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2'), (SELECT id FROM users WHERE name = 'Dan'), '2026-10-05T09:00:00Z' WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2'), 'Hotel', 36000, '2026-10-10', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), '2026-10-10T12:00:00Z', '2026-10-10T12:00:00Z' WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Hotel'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 12000 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Hotel'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 12000 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Hotel'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Dan')), 12000 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2'), 'Ramen dinner', 4250, '2026-10-11', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), '2026-10-11T12:00:00Z', '2026-10-11T12:00:00Z' WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Ramen dinner'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 1417 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Ramen dinner'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 1417 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Ramen dinner'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Dan')), 1416 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2'), 'Train passes', 20000, '2026-10-12', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Dan')), '2026-10-12T12:00:00Z', '2026-10-12T12:00:00Z' WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Train passes'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 10000 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Train passes'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 10000 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2'), 'Souvenirs', 7001, '2026-10-14', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), '2026-10-14T12:00:00Z', '2026-10-14T12:00:00Z' WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Souvenirs'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 3501 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND description = 'Souvenirs'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Dan')), 3500 WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);
INSERT INTO payments (group_id, sender_id, receiver_id, amount, payment_date, note, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Dan')), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'TOK-7KQ2') AND user_id = (SELECT id FROM users WHERE name = 'Alice')), 10000, '2026-10-15', 'Hotel and train', '2026-10-15T12:00:00Z', '2026-10-15T12:00:00Z' WHERE 'TOK-7KQ2' IN (SELECT code FROM seed_new);

-- Ski weekend (EUR)
INSERT OR IGNORE INTO groups (name, currency, invite_code, created_at)
  VALUES ('Ski weekend', 'EUR', 'SKI-W3KN', '2026-02-06T09:00:00Z');
INSERT INTO members (group_id, user_id, joined_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN'), (SELECT id FROM users WHERE name = 'Bob'), '2026-02-06T09:00:00Z' WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);
INSERT INTO members (group_id, user_id, joined_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN'), (SELECT id FROM users WHERE name = 'Carla'), '2026-02-06T09:00:00Z' WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN'), 'Ski passes', 12000, '2026-02-07', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), '2026-02-07T12:00:00Z', '2026-02-07T12:00:00Z' WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND description = 'Ski passes'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 6000 WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND description = 'Ski passes'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), 6000 WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);
INSERT INTO expenses (group_id, description, amount, expense_date, payer_id, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN'), 'Chalet', 20001, '2026-02-08', (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), '2026-02-08T12:00:00Z', '2026-02-08T12:00:00Z' WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND description = 'Chalet'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), 10001 WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);
INSERT INTO expense_shares (expense_id, member_id, share)
  SELECT (SELECT id FROM expenses WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND description = 'Chalet'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), 10000 WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);
INSERT INTO payments (group_id, sender_id, receiver_id, amount, payment_date, note, created_at, updated_at)
  SELECT (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN'), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND user_id = (SELECT id FROM users WHERE name = 'Bob')), (SELECT id FROM members WHERE group_id = (SELECT id FROM groups WHERE invite_code = 'SKI-W3KN') AND user_id = (SELECT id FROM users WHERE name = 'Carla')), 4001, '2026-02-09', 'Settled up', '2026-02-09T12:00:00Z', '2026-02-09T12:00:00Z' WHERE 'SKI-W3KN' IN (SELECT code FROM seed_new);

DROP TABLE seed_new;
