drop table public.tasks;

create table public.tasks(
	taskid text primary key,
	url text,
	status text
);

drop table public.ddls;

create table public.ddls(
	taskid text,
	statement text,
	CONSTRAINT ddls_pkey PRIMARY KEY (taskid, statement)
);

drop table public.queries;

CREATE TABLE public.queries (
	queryid text NOT NULL,
	taskid text NULL,
	runquantity int4 NULL,
	executiontime int4 NULL,
	query text NULL,
	CONSTRAINT queries_pkey PRIMARY KEY (taskid, queryid)
);

drop table public.result_ddls;

create table public.result_ddls(
	taskid text,
	statement text,
	CONSTRAINT result_ddls_pkey PRIMARY KEY (taskid, statement)
);

drop table public.result_migrations;

create table public.result_migrations(
	taskid text,
	statement text,
	CONSTRAINT result_migrations_pkey PRIMARY KEY (taskid, statement)
);

drop table public.result_queries;

create table public.result_queries(
	taskid text,
	queryid text,
	query text,
	CONSTRAINT result_queries_pkey PRIMARY KEY (taskid, queryid)
);