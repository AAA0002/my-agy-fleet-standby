import { table, integer, text, boolean, json, index, sql } from 'sdk/db';

export const adminUsers = table('admin_users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  tgId: integer('tg_id').unique().notNull(),
  name: text('name').notNull(),
  role: text('role').default('superadmin'),
  createdAt: integer('created_at', { mode: 'timestamp' }).default(sql`(unixepoch())`),
});

export const loginSessions = table('login_sessions', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  chatId: text('chat_id').unique().notNull(),
  step: text('step').notNull(), // 'WAITING_PHONE', 'WAITING_CODE', 'WAITING_2FA'
  phone: text('phone'),
  phoneCodeHash: text('phone_code_hash'),
  accountIndex: integer('account_index'),
  nodeUrl: text('node_url'),
  meta: json('meta'),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).default(sql`(unixepoch())`),
});

export const accountsCache = table('accounts_cache', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: text('user_id').unique().notNull(),
  accountIndex: integer('account_index'),
  name: text('name').notNull(),
  phone: text('phone'),
  username: text('username'),
  status: text('status').default('active'),
  wallets: json('wallets'),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).default(sql`(unixepoch())`),
}, (t) => ({
  idxAccountIndex: index('idx_accounts_index').on(t.accountIndex),
}));

export const telemetryEvents = table('telemetry_events', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  eventType: text('event_type').notNull(),
  details: json('details'),
  createdAt: integer('created_at', { mode: 'timestamp' }).default(sql`(unixepoch())`),
});
