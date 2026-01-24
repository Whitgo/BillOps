# BillOps Data Model (Phase 1 Draft)

Goals: cover core billing/time capture, support RBAC, auditability, and future integrations. Target: Postgres.

## Entities
- Users: account identity, roles, OAuth linkage.
- Clients: billable organizations/people.
- Projects: workstreams under clients.
- Time Entries: captured or manual entries tied to projects and billing rules.
- Billing Rules: rate logic per project (hourly, fixed, retainer), rounding, caps, overtime.
- Invoices: header + line items, references time/billing rules snapshots.
- Payments: settlement against invoices.
- Audit Logs: key changes to configs and authentication events.
- Sessions: login sessions (for server-managed sessions) and OAuth tokens.

## Tables (DDL Sketch)

```sql
-- Users
create table users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  password_hash text,                 -- null when using SSO-only accounts
  full_name text,
  role text not null default 'member', -- admin | member | viewer
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_login_at timestamptz
);

create table user_oauth_accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  provider text not null,              -- google | microsoft
  provider_account_id text not null,
  access_token text,
  refresh_token text,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  unique(provider, provider_account_id)
);

-- Clients
create table clients (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  currency text not null default 'USD',
  contact_email text,
  contact_name text,
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Projects
create table projects (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references clients(id) on delete cascade,
  name text not null,
  status text not null default 'active', -- active | on_hold | archived
  default_billing_rule_id uuid references billing_rules(id), -- set post create
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Billing Rules
create table billing_rules (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  rule_type text not null,        -- hourly | fixed | retainer
  rate_cents integer not null,    -- hourly or fixed amount per period
  currency text not null default 'USD',
  rounding_increment_minutes integer default 0, -- 0 means none
  overtime_multiplier numeric(6,2) default 1.0,
  cap_hours numeric(12,2),        -- optional cap per period
  retainer_hours numeric(12,2),   -- for retainer allowance
  effective_from date not null default current_date,
  effective_to date,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Time Entries
create table time_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete restrict,
  project_id uuid not null references projects(id) on delete restrict,
  client_id uuid not null references clients(id) on delete restrict,
  billing_rule_id uuid references billing_rules(id),
  source text not null,           -- auto | manual | imported
  started_at timestamptz not null,
  ended_at timestamptz not null,
  duration_minutes integer generated always as (
    extract(epoch from (ended_at - started_at)) / 60
  ) stored,
  description text,
  status text not null default 'pending', -- pending | approved | rejected | billed
  context jsonb default '{}'::jsonb,      -- app name, calendar event, file path, etc.
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (ended_at > started_at)
);

create index on time_entries (project_id, started_at);
create index on time_entries (user_id, started_at);
create index on time_entries (status);

-- Invoices
create table invoices (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references clients(id) on delete restrict,
  project_id uuid references projects(id) on delete set null,
  invoice_number text not null unique,
  currency text not null default 'USD',
  status text not null default 'draft', -- draft | sent | paid | partial | overdue | canceled
  issue_date date not null default current_date,
  due_date date,
  subtotal_cents integer not null default 0,
  tax_cents integer not null default 0,
  total_cents integer not null default 0,
  notes text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table invoice_line_items (
  id uuid primary key default gen_random_uuid(),
  invoice_id uuid not null references invoices(id) on delete cascade,
  time_entry_id uuid references time_entries(id) on delete set null,
  description text not null,
  quantity numeric(12,2) not null,
  unit_price_cents integer not null,
  amount_cents integer not null,
  billing_rule_snapshot jsonb not null default '{}'::jsonb
);

-- Payments
create table payments (
  id uuid primary key default gen_random_uuid(),
  invoice_id uuid not null references invoices(id) on delete cascade,
  amount_cents integer not null,
  method text,                    -- ach | card | wire | check | other
  received_at timestamptz not null default now(),
  reference text,
  created_at timestamptz not null default now()
);

-- Sessions (for server-managed sessions)
create table sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  session_token text not null unique,
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

-- Audit Logs
create table audit_logs (
  id bigint generated always as identity primary key,
  user_id uuid references users(id),
  actor_email text,
  action text not null,             -- e.g., create_project, update_rule, login
  entity_type text not null,
  entity_id uuid,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

## ERD Notes
- Users 1..* Projects (creator), 1..* Time Entries; Users link to OAuth accounts; Sessions tie to Users.
- Clients 1..* Projects; Projects 1..* Billing Rules; Billing Rules optional on Time Entries (resolved at approval/export time).
- Time Entries 1..* Invoice Line Items (optional via billing run); Invoices 1..* Payments.
- Audit Logs reference many entities; keep generalized meta for diffs/snapshots.

## Referential Safeguards
- Restrict deletes for users/clients/projects when time entries exist; use archival flags instead of hard delete.
- Projects cascade delete to billing rules, but restrict if time entries exist unless archived state.
- Invoice line items keep billing_rule_snapshot to maintain historical accuracy even if rules change.

## Indexing & Performance
- Time entries: composite indexes on project_id+started_at and user_id+started_at; status for workflow queues.
- Invoices: index on client_id, status, due_date; payments on invoice_id.
- Billing rules: index on project_id, effective_from/effective_to for fast lookup of active rule.

## Derived Views (future)
- Aggregates for dashboard: daily_time_by_project, revenue_by_client, ar_aging views/materialized views.
- Denormalized time_entry_export view that joins user/client/project/rule for reporting.

## Open Questions
- Do we need organizations/teams above users? (If yes, add orgs + memberships + invitations.)
- Tax handling per client vs per invoice? (Add tax_rate fields if needed.)
- Multi-currency support beyond single-currency per client? (Would require fx rates.)
- Payment providers integration (Stripe/etc.) vs manual payments only in MVP.
- Retainer period definition (monthly vs custom period); store period start anchors.
