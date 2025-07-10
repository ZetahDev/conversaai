import React from 'react';
import type { PerformanceMetrics, UserActivity } from '../../types/api';

interface PerformanceMetricsProps {
  data: PerformanceMetrics;
  userActivity: UserActivity;
  loading?: boolean;
}

export default function PerformanceMetrics({ data, userActivity, loading }: PerformanceMetricsProps) {
  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  // Calcular estadísticas de configuración
  const totalChatbots = data.model_configurations.reduce((sum, config) => sum + config.count, 0);
  const avgTemperature = data.model_configurations.reduce((sum, config) => 
    sum + (config.avg_temperature * config.count), 0) / totalChatbots;
  const avgMaxTokens = data.model_configurations.reduce((sum, config) => 
    sum + (config.avg_max_tokens * config.count), 0) / totalChatbots;

  // Top usuarios más activos
  const topUsers = userActivity.user_activity
    .sort((a, b) => b.chatbot_count - a.chatbot_count)
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Estadísticas generales de rendimiento */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-50 mr-4">
              <span className="text-2xl">🌡️</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Temperatura Promedio</p>
              <p className="text-2xl font-bold text-blue-600">
                {avgTemperature.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-50 mr-4">
              <span className="text-2xl">🎯</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Tokens Promedio</p>
              <p className="text-2xl font-bold text-green-600">
                {Math.round(avgMaxTokens)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-50 mr-4">
              <span className="text-2xl">👥</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Usuarios Activos</p>
              <p className="text-2xl font-bold text-purple-600">
                {userActivity.total_active_users}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Configuraciones por modelo */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">
          Configuraciones por Modelo
        </h3>
        
        <div className="space-y-4">
          {data.model_configurations.map((config, index) => {
            const percentage = (config.count / totalChatbots) * 100;
            const modelColors = [
              'bg-purple-500',
              'bg-blue-500',
              'bg-green-500',
              'bg-yellow-500',
              'bg-red-500'
            ];
            const bgColors = [
              'bg-purple-50',
              'bg-blue-50',
              'bg-green-50',
              'bg-yellow-50',
              'bg-red-50'
            ];
            
            return (
              <div key={config.model} className={`${bgColors[index % bgColors.length]} rounded-lg p-4`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <div className={`w-4 h-4 ${modelColors[index % modelColors.length]} rounded mr-3`}></div>
                    <h4 className="font-medium text-gray-900">{config.model}</h4>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-bold text-gray-900">{config.count}</span>
                    <span className="text-sm text-gray-600 ml-1">
                      ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Temperatura</p>
                    <p className="font-medium">{config.avg_temperature.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Max Tokens</p>
                    <p className="font-medium">{Math.round(config.avg_max_tokens)}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Uso</p>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div 
                        className={`h-2 rounded-full ${modelColors[index % modelColors.length]}`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Chatbots más nuevos y actividad de usuarios */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chatbots más nuevos */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Chatbots Más Recientes
          </h4>
          <div className="space-y-3">
            {data.newest_chatbots.map((chatbot, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900 truncate">
                    {chatbot.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(chatbot.created_at).toLocaleDateString('es-ES', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
                <div className="text-right ml-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    {chatbot.age_days < 1 ? 'Hoy' : `${Math.floor(chatbot.age_days)}d`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top usuarios activos */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Usuarios Más Activos
          </h4>
          <div className="space-y-3">
            {topUsers.map((user, index) => {
              const maxChatbots = topUsers[0]?.chatbot_count || 1;
              const percentage = (user.chatbot_count / maxChatbots) * 100;
              const rankColors = [
                'text-yellow-600 bg-yellow-50',
                'text-gray-600 bg-gray-50',
                'text-orange-600 bg-orange-50',
                'text-blue-600 bg-blue-50',
                'text-purple-600 bg-purple-50'
              ];
              
              return (
                <div key={user.user_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full ${rankColors[index]} flex items-center justify-center mr-3`}>
                      <span className="text-sm font-bold">#{index + 1}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Usuario {user.user_id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-gray-500">
                        Última actividad: {new Date(user.last_activity).toLocaleDateString('es-ES')}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">{user.chatbot_count}</p>
                    <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                      <div 
                        className="h-2 bg-blue-500 rounded-full"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Análisis de eficiencia */}
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-md font-semibold text-gray-900 mb-4">
          Análisis de Eficiencia
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {data.model_configurations.length}
            </div>
            <div className="text-sm text-gray-600">Modelos en Uso</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {((avgTemperature / 1.0) * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">Creatividad Promedio</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600 mb-1">
              {Math.round(avgMaxTokens / 100)}
            </div>
            <div className="text-sm text-gray-600">Complejidad (x100)</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600 mb-1">
              {(totalChatbots / userActivity.total_active_users).toFixed(1)}
            </div>
            <div className="text-sm text-gray-600">Bots por Usuario</div>
          </div>
        </div>
        
        {/* Recomendaciones */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h5 className="font-medium text-blue-900 mb-2">💡 Recomendaciones</h5>
          <ul className="text-sm text-blue-800 space-y-1">
            {avgTemperature > 0.8 && (
              <li>• Considera reducir la temperatura promedio para respuestas más consistentes</li>
            )}
            {avgMaxTokens > 1000 && (
              <li>• Los tokens promedio son altos, considera optimizar para reducir costos</li>
            )}
            {userActivity.total_active_users < 5 && (
              <li>• Pocos usuarios activos, considera capacitación o onboarding</li>
            )}
            {data.model_configurations.length === 1 && (
              <li>• Usando solo un modelo, considera diversificar para diferentes casos de uso</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
