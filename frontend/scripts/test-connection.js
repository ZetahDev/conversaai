#!/usr/bin/env node

// Script para probar la conexión entre frontend y backend
import fetch from 'node-fetch';

const API_BASE_URL = 'http://localhost:8000';

async function testConnection() {
  console.log('🔗 Probando conexión con el backend...');
  console.log(`📡 URL: ${API_BASE_URL}`);
  console.log('=' * 50);

  try {
    // Test 1: Health check
    console.log('\n1️⃣ Probando health check...');
    const healthResponse = await fetch(`${API_BASE_URL}/health`);
    
    if (healthResponse.ok) {
      const healthData = await healthResponse.json();
      console.log('✅ Health check exitoso:', healthData);
    } else {
      console.log('❌ Health check falló:', healthResponse.status);
    }

    // Test 2: API docs
    console.log('\n2️⃣ Probando documentación API...');
    const docsResponse = await fetch(`${API_BASE_URL}/docs`);
    
    if (docsResponse.ok) {
      console.log('✅ Documentación API disponible');
    } else {
      console.log('❌ Documentación API no disponible:', docsResponse.status);
    }

    // Test 3: Login con credenciales de prueba
    console.log('\n3️⃣ Probando login...');
    const loginResponse = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'admin@techcorp.com',
        password: 'admin123'
      })
    });

    if (loginResponse.ok) {
      const loginData = await loginResponse.json();
      console.log('✅ Login exitoso');
      console.log('🔑 Token obtenido:', loginData.access_token ? 'Sí' : 'No');
      
      // Test 4: Obtener información del usuario
      if (loginData.access_token) {
        console.log('\n4️⃣ Probando obtener información del usuario...');
        const userResponse = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${loginData.access_token}`
          }
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          console.log('✅ Información del usuario obtenida:');
          console.log(`   📧 Email: ${userData.email}`);
          console.log(`   👤 Nombre: ${userData.full_name}`);
          console.log(`   🏢 Rol: ${userData.role}`);
        } else {
          console.log('❌ Error obteniendo información del usuario:', userResponse.status);
        }

        // Test 5: Obtener chatbots
        console.log('\n5️⃣ Probando obtener chatbots...');
        const chatbotsResponse = await fetch(`${API_BASE_URL}/api/v1/chatbots/`, {
          headers: {
            'Authorization': `Bearer ${loginData.access_token}`
          }
        });

        if (chatbotsResponse.ok) {
          const chatbotsData = await chatbotsResponse.json();
          console.log('✅ Chatbots obtenidos:');
          console.log(`   🤖 Total: ${chatbotsData.items?.length || 0}`);
          if (chatbotsData.items?.length > 0) {
            chatbotsData.items.forEach((bot, index) => {
              console.log(`   ${index + 1}. ${bot.name} (${bot.status})`);
            });
          }
        } else {
          console.log('❌ Error obteniendo chatbots:', chatbotsResponse.status);
        }
      }
    } else {
      const errorData = await loginResponse.json().catch(() => ({}));
      console.log('❌ Login falló:', loginResponse.status);
      console.log('📝 Error:', errorData.detail || 'Error desconocido');
    }

    console.log('\n🎉 Pruebas de conexión completadas');

  } catch (error) {
    console.error('❌ Error durante las pruebas:', error.message);
    console.log('\n💡 Posibles soluciones:');
    console.log('   1. Verificar que el backend esté ejecutándose en http://localhost:8000');
    console.log('   2. Verificar que la base de datos esté inicializada');
    console.log('   3. Verificar las credenciales de prueba');
  }
}

async function checkBackendStatus() {
  console.log('🔍 Verificando estado del backend...');
  
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      timeout: 5000
    });
    
    if (response.ok) {
      console.log('✅ Backend está funcionando');
      return true;
    } else {
      console.log('❌ Backend responde pero con error:', response.status);
      return false;
    }
  } catch (error) {
    console.log('❌ Backend no está disponible:', error.message);
    console.log('\n🚀 Para iniciar el backend:');
    console.log('   cd backend');
    console.log('   python scripts/start_dev.py');
    return false;
  }
}

async function main() {
  console.log('🎯 ChatBot SAAS - Test de Conexión Frontend-Backend');
  console.log('=' * 60);

  const backendRunning = await checkBackendStatus();
  
  if (backendRunning) {
    await testConnection();
  } else {
    console.log('\n⏸️ Pruebas canceladas - Backend no disponible');
  }
}

// Ejecutar si es llamado directamente
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}
