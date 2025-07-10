import React from 'react';
import type { UsageTrends } from '../../types/api';

interface UsageTrendsProps {
  data: UsageTrends;
  loading?: boolean;
}

export default function UsageTrends({ data, loading }: UsageTrendsProps) {
  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(2)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  // Combinar datos para el gráfico
  const combinedData = data.creation_trend.map(item => {
    const updateItem = data.update_trend.find(u => u.date === item.date);
    return {
      date: item.date,
      created: item.created,
      updated: updateItem?.updated || 0
    };
  });

  // Estadísticas resumidas
  const totalCreated = data.creation_trend.reduce((sum, item) => sum + item.created, 0);
  const totalUpdated = data.update_trend.reduce((sum, item) => sum + item.updated, 0);
  const avgCreatedPerDay = totalCreated / data.period_days;
  const avgUpdatedPerDay = totalUpdated / data.period_days;

  // Encontrar picos de actividad
  const maxCreated = Math.max(...data.creation_trend.map(item => item.created));
  const maxUpdated = Math.max(...data.update_trend.map(item => item.updated));
  const peakCreationDay = data.creation_trend.find(item => item.created === maxCreated);
  const peakUpdateDay = data.update_trend.find(item => item.updated === maxUpdated);

  return (
    <div className="space-y-6">
      {/* Estadísticas resumidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-50 mr-4">
              <span className="text-2xl">➕</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Total Creados</p>
              <p className="text-2xl font-bold text-green-600">{totalCreated}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-50 mr-4">
              <span className="text-2xl">✏️</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Total Actualizados</p>
              <p className="text-2xl font-bold text-blue-600">{totalUpdated}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-50 mr-4">
              <span className="text-2xl">📊</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Promedio/Día</p>
              <p className="text-2xl font-bold text-purple-600">{avgCreatedPerDay.toFixed(1)}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-orange-50 mr-4">
              <span className="text-2xl">📈</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Período</p>
              <p className="text-2xl font-bold text-orange-600">{data.period_days}d</p>
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico de tendencias */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">
          Tendencias de Uso (Últimos {data.period_days} días)
        </h3>
        
        {/* Gráfico simple con CSS */}
        <div className="space-y-4">
          {/* Leyenda */}
          <div className="flex items-center space-x-6 mb-4">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
              <span className="text-sm text-gray-600">Chatbots Creados</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
              <span className="text-sm text-gray-600">Chatbots Actualizados</span>
            </div>
          </div>

          {/* Gráfico de barras simple */}
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {combinedData.slice(-14).map((item, index) => {
              const maxValue = Math.max(maxCreated, maxUpdated);
              const createdWidth = maxValue > 0 ? (item.created / maxValue) * 100 : 0;
              const updatedWidth = maxValue > 0 ? (item.updated / maxValue) * 100 : 0;
              
              return (
                <div key={index} className="flex items-center space-x-4">
                  <div className="w-20 text-xs text-gray-600 text-right">
                    {new Date(item.date).toLocaleDateString('es-ES', {
                      month: 'short',
                      day: 'numeric'
                    })}
                  </div>
                  
                  <div className="flex-1 space-y-1">
                    {/* Barra de creados */}
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-3 relative">
                        <div 
                          className="bg-green-500 h-3 rounded-full"
                          style={{ width: `${createdWidth}%` }}
                        ></div>
                        {item.created > 0 && (
                          <span className="absolute right-2 top-0 text-xs text-white font-medium">
                            {item.created}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Barra de actualizados */}
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-3 relative">
                        <div 
                          className="bg-blue-500 h-3 rounded-full"
                          style={{ width: `${updatedWidth}%` }}
                        ></div>
                        {item.updated > 0 && (
                          <span className="absolute right-2 top-0 text-xs text-white font-medium">
                            {item.updated}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Insights y picos de actividad */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Picos de Actividad
          </h4>
          <div className="space-y-4">
            {peakCreationDay && (
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-green-800">
                    Mayor creación
                  </p>
                  <p className="text-xs text-green-600">
                    {new Date(peakCreationDay.date).toLocaleDateString('es-ES')}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-green-600">
                    {peakCreationDay.created}
                  </p>
                  <p className="text-xs text-green-600">chatbots</p>
                </div>
              </div>
            )}
            
            {peakUpdateDay && (
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-blue-800">
                    Mayor actualización
                  </p>
                  <p className="text-xs text-blue-600">
                    {new Date(peakUpdateDay.date).toLocaleDateString('es-ES')}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-blue-600">
                    {peakUpdateDay.updated}
                  </p>
                  <p className="text-xs text-blue-600">chatbots</p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold text-gray-900 mb-4">
            Análisis de Tendencias
          </h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Actividad promedio</span>
              <span className="text-sm font-medium">
                {(avgCreatedPerDay + avgUpdatedPerDay).toFixed(1)} ops/día
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Ratio creación/actualización</span>
              <span className="text-sm font-medium">
                {totalUpdated > 0 ? (totalCreated / totalUpdated).toFixed(1) : '∞'}:1
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Días con actividad</span>
              <span className="text-sm font-medium">
                {combinedData.filter(item => item.created > 0 || item.updated > 0).length}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Eficiencia</span>
              <span className="text-sm font-medium">
                {totalCreated > 0 ? ((totalCreated / (totalCreated + totalUpdated)) * 100).toFixed(1) : 0}% nuevos
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
