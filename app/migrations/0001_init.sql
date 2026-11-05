-- Schema of the bootstrap features: users, groups, members, expenses, expense_shares, payments.

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK (length(name) BETWEEN 1 AND 30),
  created_at TEXT NOT NULL
);

CREATE TABLE groups (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 50),
  currency TEXT NOT NULL,
  invite_code TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE members (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  joined_at TEXT NOT NULL,
  UNIQUE (group_id, user_id)
);
CREATE INDEX members_user_idx ON members (user_id);

CREATE TABLE expenses (
  id INTEGER PRIMARY KEY,
  group_id INTEGER NOT NULL REFERENCES groups(id),
  description TEXT NOT NULL CHECK (length(description) BETWEEN 1 AND 100),
  amount INTEGER NOT NULL CHECK (amount > 0),
  expense_date TEXT NOT NULL,
  payer_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX expenses_group_idx ON expenses (group_id, expense_date);
CREATE INDEX expenses_payer_idx ON expenses (payer_id);

CREATE TABLE expense_shares (
  expense_id INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
  member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
  share INTEGER NOT NULL CHECK (share >= 0),
  PRIMARY KEY (expense_id, member_id)
);
CREATE INDEX expense_shares_member_idx ON expense_shares (member_id);

CREATE TABLE payments (
  id INTEGER PRIMARY KEY,
  group_id INTEGER NOT NULL REFERENCES groups(id),
  sender_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
  receiver_id INTEGER NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
  amount INTEGER NOT NULL CHECK (amount > 0),
  payment_date TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT '' CHECK (length(note) <= 100),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (sender_id <> receiver_id)
);
CREATE INDEX payments_group_idx ON payments (group_id, payment_date);
CREATE INDEX payments_sender_idx ON payments (sender_id);
CREATE INDEX payments_receiver_idx ON payments (receiver_id);
