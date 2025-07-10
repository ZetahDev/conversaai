import React from 'react';
import type { DashboardOverview } from '../../types/api';

interface DashboardOverviewProps {
  data: DashboardOverview;
  loading?: boolean;
}

export default function DashboardOverview({ data, loading }: DashboardOverviewProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  const stats = [
    {
      title: 'Total Chatbots',
      value: data.total_chatbots,
      icon: '🤖',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Chatbots Activos',
      value: data.active_chatbots,
      icon: '✅',
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'En Borrador',
      value: data.draft_chatbots,
      icon: '📝',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50'
    },
    {
      title: 'Actividad Reciente',
      value: data.recent_activity.length,
      icon: '📊',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Estadísticas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`p-3 rounded-full ${stat.bgColor} mr-4`}>
                <span className="text-2xl">{stat.icon}</span>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Distribución por Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Distribución por Status
          </h3>
          <div className="space-y-3">
            {Object.entries(data.status_distribution).map(([status, count]) => {
              const percentage = (count / data.total_chatbots) * 100;
              const statusColors: Record<string, string> = {
                'ACTIVE': 'bg-green-500',
                'DRAFT': 'bg-yellow-500',
                'INACTIVE': 'bg-gray-500',
                'ARCHIVED': 'bg-red-500'
              };
              
              return (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full ${statusColors[status] || 'bg-gray-400'} mr-3`}></div>
                    <span className="text-sm font-medium text-gray-700">{status}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm text-gray-600 mr-2">{count}</span>
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${statusColors[status] || 'bg-gray-400'}`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500 ml-2">{percentage.toFixed(1)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Distribución por Modelo */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Distribución por Modelo
          </h3>
          <div className="space-y-3">
            {Object.entries(data.model_distribution).map(([model, count]) => {
              const percentage = (count / data.total_chatbots) * 100;
              const modelColors: Record<string, string> = {
                'gpt-4': 'bg-purple-500',
                'gpt-3.5-turbo': 'bg-blue-500',
                'claude-3-sonnet': 'bg-orange-500',
                'claude-3-haiku': 'bg-teal-500'
              };
              
              return (
                <div key={model} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full ${modelColors[model] || 'bg-gray-400'} mr-3`}></div>
                    <span className="text-sm font-medium text-gray-700">{model}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm text-gray-600 mr-2">{count}</span>
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${modelColors[model] || 'bg-gray-400'}`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500 ml-2">{percentage.toFixed(1)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Actividad Reciente */}
      {data.recent_activity.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Actividad Reciente (Últimos 7 días)
          </h3>
          <div className="space-y-2">
            {data.recent_activity.slice(0, 7).map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                <span className="text-sm text-gray-600">
                  {new Date(activity.date).toLocaleDateString('es-ES', {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric'
                  })}
                </span>
                <div className="flex items-center">
                  <span className="text-sm font-medium text-gray-900 mr-2">
                    {activity.count} chatbots creados
                  </span>
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className="h-2 bg-blue-500 rounded-full"
                      style={{ 
                        width: `${Math.min((activity.count / Math.max(...data.recent_activity.map(a => a.count))) * 100, 100)}%` 
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
