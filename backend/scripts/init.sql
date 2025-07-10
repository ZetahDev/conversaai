-- Script de inicialización de la base de datos PostgreSQL

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Crear función para obtener el tenant actual (para RLS)
CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS INTEGER AS $$
BEGIN
    RETURN COALESCE(current_setting('app.current_tenant_id', true)::INTEGER, 0);
END;
$$ LANGUAGE plpgsql STABLE;

-- Crear función para generar slugs
CREATE OR REPLACE FUNCTION generate_slug(input_text TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN lower(
        regexp_replace(
            regexp_replace(
                unaccent(trim(input_text)),
                '[^a-zA-Z0-9\s-]', '', 'g'
            ),
            '\s+', '-', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Crear función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear función para soft delete
CREATE OR REPLACE FUNCTION soft_delete_record()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE companies SET 
        is_deleted = true,
        deleted_at = CURRENT_TIMESTAMP
    WHERE id = OLD.company_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Crear índices para búsqueda de texto completo
CREATE TEXT SEARCH CONFIGURATION spanish_unaccent (COPY = spanish);
ALTER TEXT SEARCH CONFIGURATION spanish_unaccent
    ALTER MAPPING FOR hword, hword_part, word
    WITH unaccent, spanish_stem;

-- Crear función para búsqueda de texto
CREATE OR REPLACE FUNCTION search_text(
    search_query TEXT,
    target_text TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN to_tsvector('spanish_unaccent', target_text) @@ 
           plainto_tsquery('spanish_unaccent', search_query);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Crear función para logging de auditoría
CREATE OR REPLACE FUNCTION audit_log_changes()
RETURNS TRIGGER AS $$
DECLARE
    audit_data JSONB;
BEGIN
    -- Preparar datos de auditoría
    audit_data = jsonb_build_object(
        'table_name', TG_TABLE_NAME,
        'operation', TG_OP,
        'timestamp', CURRENT_TIMESTAMP,
        'user_id', current_setting('app.current_user_id', true),
        'tenant_id', current_setting('app.current_tenant_id', true)
    );
    
    -- Agregar datos según la operación
    IF TG_OP = 'DELETE' THEN
        audit_data = audit_data || jsonb_build_object('old_data', row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        audit_data = audit_data || jsonb_build_object(
            'old_data', row_to_json(OLD),
            'new_data', row_to_json(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        audit_data = audit_data || jsonb_build_object('new_data', row_to_json(NEW));
        RETURN NEW;
    END IF;
    
    -- Insertar en tabla de auditoría (se creará con Alembic)
    -- INSERT INTO audit_logs (data) VALUES (audit_data);
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Crear función para validar email
CREATE OR REPLACE FUNCTION is_valid_email(email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Crear función para generar API keys
CREATE OR REPLACE FUNCTION generate_api_key()
RETURNS TEXT AS $$
BEGIN
    RETURN 'cb_' || encode(gen_random_bytes(32), 'base64');
END;
$$ LANGUAGE plpgsql;

-- Crear función para hash de passwords (placeholder - se usará bcrypt en Python)
CREATE OR REPLACE FUNCTION hash_password(password TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Esta función es un placeholder
    -- El hash real se hace en Python con bcrypt
    RETURN 'hashed_' || password;
END;
$$ LANGUAGE plpgsql;

-- Crear función para limpiar datos antiguos
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS VOID AS $$
BEGIN
    -- Limpiar logs antiguos (más de 90 días)
    DELETE FROM usage_logs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    -- Limpiar sesiones expiradas
    DELETE FROM user_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Limpiar tokens expirados
    DELETE FROM refresh_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    RAISE NOTICE 'Cleanup completed at %', CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Crear función para estadísticas de uso
CREATE OR REPLACE FUNCTION get_usage_stats(company_id_param INTEGER)
RETURNS TABLE(
    total_messages INTEGER,
    total_conversations INTEGER,
    active_chatbots INTEGER,
    monthly_messages INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(CASE WHEN m.created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 ELSE 0 END), 0)::INTEGER as total_messages,
        COUNT(DISTINCT c.id)::INTEGER as total_conversations,
        COUNT(DISTINCT cb.id)::INTEGER as active_chatbots,
        COALESCE(SUM(CASE WHEN m.created_at >= date_trunc('month', CURRENT_DATE) THEN 1 ELSE 0 END), 0)::INTEGER as monthly_messages
    FROM companies comp
    LEFT JOIN chatbots cb ON cb.company_id = comp.id AND cb.is_deleted = false
    LEFT JOIN conversations c ON c.chatbot_id = cb.id AND c.is_deleted = false
    LEFT JOIN messages m ON m.conversation_id = c.id AND m.is_deleted = false
    WHERE comp.id = company_id_param AND comp.is_deleted = false;
END;
$$ LANGUAGE plpgsql;

-- Crear roles de base de datos
DO $$
BEGIN
    -- Rol para la aplicación
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'chatbot_app') THEN
        CREATE ROLE chatbot_app WITH LOGIN PASSWORD 'app_password';
    END IF;
    
    -- Rol de solo lectura
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'chatbot_readonly') THEN
        CREATE ROLE chatbot_readonly WITH LOGIN PASSWORD 'readonly_password';
    END IF;
END
$$;

-- Configurar permisos básicos
GRANT CONNECT ON DATABASE chatbot_db TO chatbot_app;
GRANT CONNECT ON DATABASE chatbot_db TO chatbot_readonly;

-- Configurar esquema por defecto
ALTER DATABASE chatbot_db SET search_path TO public;

-- Configurar timezone por defecto
ALTER DATABASE chatbot_db SET timezone TO 'UTC';

-- Configurar configuración de texto completo
ALTER DATABASE chatbot_db SET default_text_search_config TO 'spanish_unaccent';

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Base de datos inicializada correctamente en %', CURRENT_TIMESTAMP;
END
$$;
