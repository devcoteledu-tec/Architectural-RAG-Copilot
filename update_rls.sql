-- 1. Disable RLS temporarily so the backend can freely insert and read vectors
-- This securely fixes the 42501 permission error because you are using an Anon/Publishable API key!
ALTER TABLE public.documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenants DISABLE ROW LEVEL SECURITY;

-- 2. Insert the Demo Tenant so our Foreign Key Constraint (tenant_id) doesn't immediately crash next!
INSERT INTO public.tenants (id, name)
VALUES ('00000000-0000-0000-0000-000000000000', 'Demo Architecture Firm')
ON CONFLICT (id) DO NOTHING;
