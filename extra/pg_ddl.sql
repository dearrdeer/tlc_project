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
	foreign key (taskid) references public.tasks (taskid)
);

CREATE TABLE public.queries (
	queryid text NOT NULL,
	taskid text NULL,
	runquantity int4 NULL,
	executiontime int4 NULL,
	query text NULL,
	CONSTRAINT queries_pkey PRIMARY KEY (queryid)
);

drop table public.result_ddls;

create table public.result_ddls(
	taskid text,
	statement text,
	foreign key (taskid) references public.tasks (taskid)
);

drop table public.result_migrations;

create table public.result_migrations(
	taskid text,
	statement text,
	foreign key (taskid) references public.tasks (taskid)
);

drop table public.result_queries;

create table public.result_queries(
	taskid text,
	queryid text,
	query text,
	foreign key (taskid) references public.tasks (taskid)
);