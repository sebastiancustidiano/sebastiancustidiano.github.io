-- =====================================================================
--  LA XVII · 22) LO QUE SE MUEVE NO VUELVE ATRÁS (24/11/2026)
--  Problema: al abrir la página, el navegador reenviaba a la base TODAS las fotos tal como las
--  tenía guardadas localmente (copia vieja). Si esa sesión era de admin, volvía a poner las fotos
--  en su álbum anterior (pasó el 24/11 entre las 10:39 y 10:42: se deshicieron 76 movimientos).
--  Arreglo en la base (protege aunque algún navegador tenga una copia vieja):
--   - El álbum de una foto SOLO cambia con la función admin_move_photos (botón «Mover» del admin).
--     Cualquier otro intento de cambiarlo se ignora en silencio (se conserva el álbum de la base).
--   - Los «me gusta» nunca bajan por una copia vieja.
--  No borra ni cambia datos. Se puede correr más de una vez.
-- =====================================================================
begin;
create or replace function public.photos_move_guard() returns trigger
language plpgsql set search_path = public as $$
begin
  if new.category is distinct from old.category and coalesce(current_setting('laxvii.mover', true), '') <> '1' then
    new.category := old.category;                    -- solo se mueve con admin_move_photos
  end if;
  if coalesce(new.likes, 0) < coalesce(old.likes, 0) then
    new.likes := old.likes;                          -- una copia vieja no baja los «me gusta»
  end if;
  return new;
end $$;
drop trigger if exists photos_move_guard on public.photos;
create trigger photos_move_guard before update on public.photos
  for each row execute function public.photos_move_guard();

create or replace function public.admin_move_photos(p_ids text[], p_dest text) returns integer
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if not public.is_admin() then raise exception 'Solo el administrador puede mover fotos de álbum.' using errcode = '42501'; end if;
  if coalesce(btrim(p_dest), '') = '' then raise exception 'Falta el álbum de destino.' using errcode = '22023'; end if;
  perform set_config('laxvii.mover', '1', true);
  update public.photos set category = p_dest where id::text = any(p_ids) and category is distinct from p_dest;
  get diagnostics n = row_count;
  perform set_config('laxvii.mover', '', true);
  return n;
end $$;
revoke all on function public.admin_move_photos(text[], text) from public, anon;
grant execute on function public.admin_move_photos(text[], text) to authenticated;
commit;
notify pgrst, 'reload schema';
