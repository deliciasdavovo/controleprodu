-- Campos e armazenamento das fotos das receitas
alter table public.recipes add column if not exists image_url text;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('recipe-photos', 'recipe-photos', true, 8388608, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = true, file_size_limit = 8388608,
allowed_mime_types = array['image/jpeg','image/png','image/webp'];

drop policy if exists "Fotos de receitas: leitura publica" on storage.objects;
create policy "Fotos de receitas: leitura publica" on storage.objects
for select to public using (bucket_id = 'recipe-photos');

drop policy if exists "Fotos de receitas: upload autenticado" on storage.objects;
create policy "Fotos de receitas: upload autenticado" on storage.objects
for insert to authenticated with check (bucket_id = 'recipe-photos');
