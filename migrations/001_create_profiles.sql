-- Create profiles table with RLS policies
create table if not exists public.profiles (
    id uuid references auth.users on delete cascade primary key,
    name text,
    avatar_url text,
    role text default 'user' check (role in ('user', 'admin')),
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Enable Row Level Security
alter table public.profiles enable row level security;

-- Create RLS policies
create policy "Public profiles are viewable by everyone"
    on profiles for select
    using ( true );

create policy "Users can insert their own profile"
    on profiles for insert
    with check ( auth.uid() = id );

create policy "Users can update own profile"
    on profiles for update
    using ( auth.uid() = id );

create policy "Admins can update any profile"
    on profiles for update
    using (
        auth.jwt() ->> 'role' = 'admin'
    );

-- Create trigger for updated_at
create or replace function public.handle_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger on_profile_update
    before update on public.profiles
    for each row
    execute procedure public.handle_updated_at();

-- Create trigger to create profile on user signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, name)
    values (new.id, new.raw_user_meta_data->>'name');
    return new;
end;
$$ language plpgsql;

create trigger on_auth_user_created
    after insert on auth.users
    for each row
    execute procedure public.handle_new_user();