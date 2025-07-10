"""
Script para migrar la tabla chatbots a la estructura completa
"""
import sqlite3
import sys
import os
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate_chatbots_table():
    """Migrar tabla chatbots a estructura completa"""
    
    db_path = "chatbot_minimal.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Iniciando migración de tabla chatbots...")
        
        # 1. Verificar estructura actual
        cursor.execute("PRAGMA table_info(chatbots)")
        current_columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"📋 Columnas actuales: {list(current_columns.keys())}")
        
        # 2. Definir columnas que necesitamos agregar
        new_columns = {
            'avatar_url': 'TEXT',
            'is_public': 'BOOLEAN DEFAULT FALSE',
            'personality': 'TEXT',
            'custom_instructions': 'TEXT',
            'greeting_message': 'TEXT',
            'fallback_message': 'TEXT',
            'primary_ai_provider': 'TEXT DEFAULT "openai"',
            'fallback_ai_provider': 'TEXT',
            'max_conversation_length': 'INTEGER DEFAULT 20',
            'response_delay_ms': 'INTEGER DEFAULT 1000',
            'enable_typing_indicator': 'BOOLEAN DEFAULT TRUE',
            'enable_context_memory': 'BOOLEAN DEFAULT TRUE',
            'enable_sentiment_analysis': 'BOOLEAN DEFAULT FALSE',
            'enable_language_detection': 'BOOLEAN DEFAULT FALSE',
            'enable_content_filter': 'BOOLEAN DEFAULT TRUE',
            'enable_rate_limiting': 'BOOLEAN DEFAULT TRUE',
            'max_messages_per_hour': 'INTEGER DEFAULT 100',
            'total_conversations': 'INTEGER DEFAULT 0',
            'total_messages': 'INTEGER DEFAULT 0',
            'average_rating': 'REAL DEFAULT 0.0',
            'custom_config': 'TEXT',
            'is_deleted': 'BOOLEAN DEFAULT FALSE',
            'deleted_at': 'TIMESTAMP',
            'updated_by': 'TEXT',
            'version': 'INTEGER DEFAULT 1'
        }
        
        # 3. Agregar columnas faltantes
        columns_added = 0
        for column_name, column_type in new_columns.items():
            if column_name not in current_columns:
                try:
                    alter_sql = f"ALTER TABLE chatbots ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    print(f"✅ Agregada columna: {column_name}")
                    columns_added += 1
                except sqlite3.Error as e:
                    print(f"❌ Error agregando columna {column_name}: {e}")
        
        # 4. Actualizar registros existentes con valores por defecto
        if columns_added > 0:
            print("🔄 Actualizando registros existentes...")
            
            # Actualizar valores por defecto para registros existentes
            update_queries = [
                "UPDATE chatbots SET is_public = FALSE WHERE is_public IS NULL",
                "UPDATE chatbots SET primary_ai_provider = 'openai' WHERE primary_ai_provider IS NULL",
                "UPDATE chatbots SET max_conversation_length = 20 WHERE max_conversation_length IS NULL",
                "UPDATE chatbots SET response_delay_ms = 1000 WHERE response_delay_ms IS NULL",
                "UPDATE chatbots SET enable_typing_indicator = TRUE WHERE enable_typing_indicator IS NULL",
                "UPDATE chatbots SET enable_context_memory = TRUE WHERE enable_context_memory IS NULL",
                "UPDATE chatbots SET enable_sentiment_analysis = FALSE WHERE enable_sentiment_analysis IS NULL",
                "UPDATE chatbots SET enable_language_detection = FALSE WHERE enable_language_detection IS NULL",
                "UPDATE chatbots SET enable_content_filter = TRUE WHERE enable_content_filter IS NULL",
                "UPDATE chatbots SET enable_rate_limiting = TRUE WHERE enable_rate_limiting IS NULL",
                "UPDATE chatbots SET max_messages_per_hour = 100 WHERE max_messages_per_hour IS NULL",
                "UPDATE chatbots SET total_conversations = 0 WHERE total_conversations IS NULL",
                "UPDATE chatbots SET total_messages = 0 WHERE total_messages IS NULL",
                "UPDATE chatbots SET average_rating = 0.0 WHERE average_rating IS NULL",
                "UPDATE chatbots SET is_deleted = FALSE WHERE is_deleted IS NULL",
                "UPDATE chatbots SET version = 1 WHERE version IS NULL"
            ]
            
            for query in update_queries:
                try:
                    cursor.execute(query)
                except sqlite3.Error as e:
                    print(f"⚠️ Warning en actualización: {e}")
        
        # 5. Verificar estructura final
        cursor.execute("PRAGMA table_info(chatbots)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Columnas finales: {len(final_columns)} columnas")
        
        # 6. Crear índices para mejorar rendimiento
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_chatbots_company_status ON chatbots(company_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_chatbots_created_by ON chatbots(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_chatbots_is_public ON chatbots(is_public)",
            "CREATE INDEX IF NOT EXISTS idx_chatbots_is_deleted ON chatbots(is_deleted)"
        ]
        
        print("🔄 Creando índices...")
        for index_sql in indices:
            try:
                cursor.execute(index_sql)
                print(f"✅ Índice creado")
            except sqlite3.Error as e:
                print(f"⚠️ Warning creando índice: {e}")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"✅ Migración completada exitosamente!")
        print(f"📊 Columnas agregadas: {columns_added}")
        print(f"📊 Total de columnas: {len(final_columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()


def verify_migration():
    """Verificar que la migración fue exitosa"""
    try:
        conn = sqlite3.connect("chatbot_minimal.db")
        cursor = conn.cursor()
        
        # Verificar estructura
        cursor.execute("PRAGMA table_info(chatbots)")
        columns = cursor.fetchall()
        
        print("\n📋 ESTRUCTURA FINAL DE LA TABLA CHATBOTS:")
        print("-" * 60)
        for col in columns:
            print(f"{col[1]:<30} {col[2]:<20} {'NOT NULL' if col[3] else 'NULL'}")
        
        # Verificar datos existentes
        cursor.execute("SELECT COUNT(*) FROM chatbots")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total de chatbots: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, name, status, primary_ai_provider FROM chatbots LIMIT 3")
            rows = cursor.fetchall()
            print("\n📋 Muestra de datos:")
            for row in rows:
                print(f"  ID: {row[0][:8]}... | Nombre: {row[1]} | Status: {row[2]} | Provider: {row[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False


if __name__ == "__main__":
    print("🚀 MIGRACIÓN DE TABLA CHATBOTS")
    print("=" * 50)
    
    # Ejecutar migración
    if migrate_chatbots_table():
        print("\n🔍 Verificando migración...")
        verify_migration()
        print("\n🎉 ¡Migración completada exitosamente!")
        print("\n📝 Próximos pasos:")
        print("1. Reiniciar el servidor backend")
        print("2. Probar los endpoints de chatbots")
        print("3. Verificar que todo funcione correctamente")
    else:
        print("\n❌ La migración falló. Revisa los errores arriba.")
        sys.exit(1)
