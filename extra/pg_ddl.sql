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

drop table public.queries;

create table public.queries(
	queryid text primary key,
	taskid text,
	runquantity int,
	executiontime int,
	query text,
	foreign key (taskid) references public.tasks (taskid)
);