import React, { useState, useEffect } from 'react';
import type { RealTimeMetrics } from '../../types/api';

interface RealTimeMetricsProps {
  data: RealTimeMetrics;
  loading?: boolean;
  onRefresh?: () => void;
}

export default function RealTimeMetrics({ data, loading, onRefresh }: RealTimeMetricsProps) {
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    setLastUpdate(new Date());
  }, [data]);

  // Auto-refresh cada 30 segundos
  useEffect(() => {
    if (onRefresh) {
      const interval = setInterval(() => {
        onRefresh();
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [onRefresh]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const realTimeStats = [
    {
      title: 'Usuarios Activos',
      value: data.current_active_users,
      icon: '👥',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      suffix: ''
    },
    {
      title: 'Requests/Hora',
      value: data.requests_last_hour,
      icon: '📈',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      suffix: ''
    },
    {
      title: 'Requests/Min',
      value: data.requests_per_minute,
      icon: '⚡',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      suffix: ''
    },
    {
      title: 'Tiempo Respuesta',
      value: data.average_response_time,
      icon: '⏱️',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      suffix: 's'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header con última actualización */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Métricas en Tiempo Real
          </h3>
          <div className="flex items-center text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            Actualizado: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>

        {/* Métricas principales */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {realTimeStats.map((stat, index) => (
            <div key={index} className={`${stat.bgColor} rounded-lg p-4`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                    {stat.title}
                  </p>
                  <p className={`text-2xl font-bold ${stat.color}`}>
                    {typeof stat.value === 'number' ? stat.value.toFixed(stat.suffix === 's' ? 3 : 0) : stat.value}
                    {stat.suffix}
                  </p>
                </div>
                <span className="text-2xl">{stat.icon}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Operaciones y Errores */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Operaciones Totales */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Operaciones por Tipo
          </h4>
          <div className="space-y-3">
            {Object.entries(data.total_operations).map(([operation, count]) => {
              const operationIcons: Record<string, string> = {
                'create': '➕',
                'update': '✏️',
                'delete': '🗑️',
                'read': '👁️'
              };
              
              const maxCount = Math.max(...Object.values(data.total_operations));
              const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
              
              return (
                <div key={operation} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-lg mr-2">{operationIcons[operation] || '📊'}</span>
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {operation}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm text-gray-600 mr-2">{count}</span>
                    <div className="w-16 bg-gray-200 rounded-full h-2">
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

        {/* Errores */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Errores por Código
          </h4>
          {Object.keys(data.error_counts).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(data.error_counts).map(([errorCode, count]) => {
                const errorColors: Record<string, string> = {
                  '400': 'bg-yellow-500',
                  '401': 'bg-orange-500',
                  '403': 'bg-red-500',
                  '404': 'bg-purple-500',
                  '429': 'bg-pink-500',
                  '500': 'bg-red-600'
                };
                
                const maxCount = Math.max(...Object.values(data.error_counts));
                const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
                
                return (
                  <div key={errorCode} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full ${errorColors[errorCode] || 'bg-gray-400'} mr-3`}></div>
                      <span className="text-sm font-medium text-gray-700">
                        Error {errorCode}
                      </span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm text-gray-600 mr-2">{count}</span>
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${errorColors[errorCode] || 'bg-gray-400'}`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-4">
              <span className="text-4xl">✅</span>
              <p className="text-sm text-gray-500 mt-2">Sin errores recientes</p>
            </div>
          )}
        </div>
      </div>

      {/* Top Modelos y Cambios Recientes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Modelos */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Modelos Más Usados
          </h4>
          <div className="space-y-3">
            {data.top_models.slice(0, 5).map(([model, count], index) => {
              const modelColors = [
                'bg-purple-500',
                'bg-blue-500',
                'bg-green-500',
                'bg-yellow-500',
                'bg-red-500'
              ];
              
              const maxCount = data.top_models.length > 0 ? data.top_models[0][1] : 1;
              const percentage = (count / maxCount) * 100;
              
              return (
                <div key={model} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full ${modelColors[index]} mr-3`}></div>
                    <span className="text-sm font-medium text-gray-700">{model}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm text-gray-600 mr-2">{count}</span>
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${modelColors[index]}`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Cambios de Status Recientes */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Cambios Recientes
          </h4>
          {data.recent_status_changes.length > 0 ? (
            <div className="space-y-3 max-h-48 overflow-y-auto">
              {data.recent_status_changes.slice(0, 5).map((change, index) => (
                <div key={index} className="flex items-center justify-between text-xs">
                  <div className="flex items-center">
                    <span className="text-gray-500">
                      {new Date(change.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-red-500">{change.old_status}</span>
                    <span className="mx-1">→</span>
                    <span className="text-green-500">{change.new_status}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4">
              <span className="text-4xl">📊</span>
              <p className="text-sm text-gray-500 mt-2">Sin cambios recientes</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
