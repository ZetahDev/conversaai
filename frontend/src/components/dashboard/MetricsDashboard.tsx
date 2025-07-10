import React, { useState, useEffect } from 'react';
import { dashboardApi } from '../../lib/api';
import type { CompleteDashboard } from '../../types/api';
import DashboardOverview from './DashboardOverview';
import RealTimeMetrics from './RealTimeMetrics';
import UsageTrends from './UsageTrends';
import PerformanceMetrics from './PerformanceMetrics';

// Tipos para las respuestas de la API
interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

interface MetricsDashboardProps {
  token: string;
}

export default function MetricsDashboard({ token }: MetricsDashboardProps) {
  const [data, setData] = useState<CompleteDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  const fetchDashboardData = async () => {
    try {
      setError(null);
      const response = await dashboardApi.getCompleteDashboard(token, 30) as ApiResponse<CompleteDashboard>;

      if (response && response.success) {
        setData(response.data);
      } else {
        // No mostrar error, simplemente indicar que no hay métricas
        setData(null);
      }
    } catch (err) {
      // Error de conexión real, mantener mensaje de error
      setError('No se pudieron cargar las métricas en este momento');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshRealTimeData = async () => {
    if (!data) return;

    try {
      const response = await dashboardApi.getRealTimeMetrics(token) as ApiResponse<any>;
      if (response && response.success) {
        setData(prev => prev ? {
          ...prev,
          real_time_metrics: response.data
        } : null);
      }
    } catch (err) {
      console.error('Error refreshing real-time data:', err);
    }
  };

  const exportData = async (format: 'json' | 'csv') => {
    try {
      const response = await dashboardApi.exportData(token, format, 30) as ApiResponse<any>;
      if (response && response.success) {
        // Crear y descargar archivo
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: format === 'json' ? 'application/json' : 'text/csv'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dashboard-metrics-${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Error exporting data:', err);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [token]);

  // Auto-refresh para métricas en tiempo real
  useEffect(() => {
    if (activeTab === 'realtime') {
      const interval = setInterval(refreshRealTimeData, 30000); // 30 segundos
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [activeTab, data]);

  const tabs = [
    { id: 'overview', name: 'Resumen', icon: '📊' },
    { id: 'realtime', name: 'Tiempo Real', icon: '⚡' },
    { id: 'trends', name: 'Tendencias', icon: '📈' },
    { id: 'performance', name: 'Rendimiento', icon: '⚙️' }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-64 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <span className="text-4xl mb-4 block">⚠️</span>
            <h3 className="text-lg font-semibold text-red-800 mb-2">
              Problema de conexión
            </h3>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchDashboardData}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Si no hay datos (sin métricas aún)
  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
            <span className="text-6xl mb-6 block">📊</span>
            <h3 className="text-2xl font-semibold text-blue-800 mb-4">
              Aún no tenemos métricas
            </h3>
            <p className="text-blue-600 mb-6 text-lg">
              Comienza creando chatbots y teniendo conversaciones para ver tus métricas aquí.
            </p>
            <div className="space-y-3">
              <a
                href="/chatbots/create"
                className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Crear mi primer chatbot
              </a>
              <p className="text-sm text-blue-500">
                Una vez que tengas conversaciones, las métricas aparecerán automáticamente
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard de Métricas</h1>
              <p className="text-gray-600 mt-1">
                Análisis completo del rendimiento y uso de chatbots
              </p>
            </div>
            
            {/* Botones de exportación */}
            <div className="flex space-x-2">
              <button
                onClick={() => exportData('json')}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
              >
                📄 Exportar JSON
              </button>
              <button
                onClick={() => exportData('csv')}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors text-sm"
              >
                📊 Exportar CSV
              </button>
              <button
                onClick={fetchDashboardData}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors text-sm"
              >
                🔄 Actualizar
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="space-y-6">
          {activeTab === 'overview' && (
            <DashboardOverview data={data.overview} />
          )}
          
          {activeTab === 'realtime' && (
            <RealTimeMetrics 
              data={data.real_time_metrics} 
              onRefresh={refreshRealTimeData}
            />
          )}
          
          {activeTab === 'trends' && (
            <UsageTrends data={data.usage_trends} />
          )}
          
          {activeTab === 'performance' && (
            <PerformanceMetrics 
              data={data.performance_metrics}
              userActivity={data.user_activity}
            />
          )}
        </div>

        {/* Footer con información */}
        <div className="mt-12 text-center text-sm text-gray-500">
          <p>
            Última actualización: {new Date().toLocaleString('es-ES')}
            {activeTab === 'realtime' && (
              <span className="ml-2">
                • <span className="text-green-600">●</span> Actualizando cada 30s
              </span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
