-- O Controle Produ acessa o Supabase com a chave pública (papel anon), como
-- nas demais tabelas. A política anterior só aceitava upload de usuário
-- autenticado, e o envio de foto pela ficha técnica falhava com
-- "new row violates row-level security policy".
drop policy if exists "Fotos de receitas: upload autenticado" on storage.objects;
drop policy if exists "Fotos de receitas: upload pelo app" on storage.objects;
create policy "Fotos de receitas: upload pelo app" on storage.objects
for insert to anon, authenticated with check (bucket_id = 'recipe-photos');
