-- 24_cvu_pago.sql · 27/11/2026 · Cuenta para transferir al fondo (BullPay), para el chatbot «El Pirata».
-- Aditivo: solo agrega/actualiza las claves "cvu" y "alias" del payload de fund_data.main.
-- admin_fund_apply / admin_fund_cerrar usan jsonb_set: conservan estas claves al guardar o cerrar.
-- Se lee con permiso Fondo (misma política que el resto de main). NO va en el HTML público.
-- Los valores reales NO se guardan en el kit: reemplazar <CVU> y <ALIAS> al aplicar.
update public.fund_data
   set payload = payload || jsonb_build_object('cvu', '<CVU>', 'alias', '<ALIAS>')
 where id = 'main';
-- Verificación:
-- select payload->>'alias' alias, length(payload->>'cvu') largo_cvu from public.fund_data where id='main';
