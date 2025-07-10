import React, { useState, useEffect } from 'react';
import { integrationsAPI, type WhatsAppConfig, type TelegramConfig, type WebWidgetConfig } from '../../lib/integrations-api';

interface IntegrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  integrationType: 'whatsapp' | 'telegram' | 'web' | null;
  token: string;
  chatbotId?: string;
}

export default function IntegrationModal({
  token,
  chatbotId = '1' // Default para testing
}: Omit<IntegrationModalProps, 'isOpen' | 'onClose' | 'integrationType'>) {
  const [isOpen, setIsOpen] = useState(false);
  const [integrationType, setIntegrationType] = useState<'whatsapp' | 'telegram' | 'web' | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // WhatsApp state
  const [whatsappConfig, setWhatsappConfig] = useState<WhatsAppConfig>({
    phone_number_id: '',
    access_token: ''
  });

  // Telegram state
  const [telegramConfig, setTelegramConfig] = useState<TelegramConfig>({
    bot_token: ''
  });

  // Web Widget state
  const [webWidgetConfig, setWebWidgetConfig] = useState<WebWidgetConfig>({
    widget_type: 'popup',
    primary_color: '#3B82F6',
    title: 'Asistente Virtual',
    subtitle: '¿En qué puedo ayudarte?',
    position: 'bottom-right'
  });
  const [generatedCode, setGeneratedCode] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setSuccess(null);
      setGeneratedCode('');
    }
  }, [isOpen, integrationType]);

  useEffect(() => {
    // Escuchar eventos para abrir el modal
    const handleOpenModal = (event: CustomEvent) => {
      const { integrationType: type } = event.detail;
      setIntegrationType(type);
      setIsOpen(true);
    };

    window.addEventListener('openIntegrationModal', handleOpenModal as EventListener);

    return () => {
      window.removeEventListener('openIntegrationModal', handleOpenModal as EventListener);
    };
  }, []);

  const onClose = () => {
    setIsOpen(false);
    setIntegrationType(null);
  };

  const handleWhatsAppSetup = async () => {
    if (!whatsappConfig.phone_number_id || !whatsappConfig.access_token) {
      setError('Por favor completa todos los campos requeridos');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await integrationsAPI.setupWhatsApp(chatbotId, whatsappConfig, token);
      setSuccess('✅ WhatsApp configurado exitosamente');
      setTimeout(() => {
        onClose();
        window.location.reload(); // Refresh para mostrar nueva integración
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error configurando WhatsApp');
    } finally {
      setLoading(false);
    }
  };

  const handleTelegramSetup = async () => {
    if (!telegramConfig.bot_token) {
      setError('Por favor ingresa el token del bot');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await integrationsAPI.setupTelegram(chatbotId, telegramConfig.bot_token, token);
      setSuccess('✅ Telegram configurado exitosamente');
      setTimeout(() => {
        onClose();
        window.location.reload(); // Refresh para mostrar nueva integración
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error configurando Telegram');
    } finally {
      setLoading(false);
    }
  };

  const handleWebWidgetGenerate = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await integrationsAPI.getWidgetCode(
        chatbotId, 
        webWidgetConfig.widget_type, 
        webWidgetConfig, 
        token
      );
      setGeneratedCode(result.code);
      setSuccess('✅ Código del widget generado');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error generando código del widget');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setSuccess('✅ Código copiado al portapapeles');
    } catch (err) {
      setError('Error copiando al portapapeles');
    }
  };

  if (!isOpen || !integrationType) return null;

  const titles = {
    whatsapp: '📱 Configurar WhatsApp Business',
    telegram: '✈️ Configurar Telegram Bot',
    web: '🌐 Configurar Widget Web'
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white dark:bg-gray-800">
        <div className="mt-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              {titles[integrationType]}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <span className="sr-only">Cerrar</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}
          
          {success && (
            <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
              {success}
            </div>
          )}

          {/* Content */}
          <div className="space-y-4">
            {integrationType === 'whatsapp' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Phone Number ID
                  </label>
                  <input
                    type="text"
                    value={whatsappConfig.phone_number_id}
                    onChange={(e) => setWhatsappConfig(prev => ({ ...prev, phone_number_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                    placeholder="Ej: 123456789012345"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Access Token
                  </label>
                  <input
                    type="password"
                    value={whatsappConfig.access_token}
                    onChange={(e) => setWhatsappConfig(prev => ({ ...prev, access_token: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                    placeholder="Token de WhatsApp Business"
                  />
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Webhook URL:</h4>
                  <code className="text-sm text-blue-700 dark:text-blue-300">
                    http://localhost:8000/api/v1/integrations/whatsapp/webhook
                  </code>
                </div>
                <button
                  onClick={handleWhatsAppSetup}
                  disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg"
                >
                  {loading ? 'Configurando...' : 'Configurar WhatsApp'}
                </button>
              </div>
            )}

            {integrationType === 'telegram' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Bot Token
                  </label>
                  <input
                    type="password"
                    value={telegramConfig.bot_token}
                    onChange={(e) => setTelegramConfig(prev => ({ ...prev, bot_token: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                    placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                  />
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">Pasos:</h4>
                  <ol className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                    <li>1. Habla con @BotFather en Telegram</li>
                    <li>2. Usa /newbot para crear tu bot</li>
                    <li>3. Copia el token que te da</li>
                    <li>4. Pégalo arriba y configura</li>
                  </ol>
                </div>
                <button
                  onClick={handleTelegramSetup}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg"
                >
                  {loading ? 'Configurando...' : 'Configurar Telegram'}
                </button>
              </div>
            )}

            {integrationType === 'web' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tipo de Widget
                  </label>
                  <select
                    value={webWidgetConfig.widget_type}
                    onChange={(e) => setWebWidgetConfig(prev => ({ ...prev, widget_type: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                  >
                    <option value="popup">Popup Flotante</option>
                    <option value="embedded">Widget Embebido</option>
                    <option value="iframe">iFrame</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Color Principal
                  </label>
                  <input
                    type="color"
                    value={webWidgetConfig.primary_color}
                    onChange={(e) => setWebWidgetConfig(prev => ({ ...prev, primary_color: e.target.value }))}
                    className="w-full h-10 border border-gray-300 dark:border-gray-600 rounded-md"
                  />
                </div>
                
                {generatedCode && (
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium text-purple-900 dark:text-purple-100">Código generado:</h4>
                      <button
                        onClick={() => copyToClipboard(generatedCode)}
                        className="text-sm bg-purple-600 text-white px-2 py-1 rounded hover:bg-purple-700"
                      >
                        Copiar
                      </button>
                    </div>
                    <textarea
                      readOnly
                      value={generatedCode}
                      className="w-full h-32 text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded border font-mono"
                    />
                  </div>
                )}
                
                <button
                  onClick={handleWebWidgetGenerate}
                  disabled={loading}
                  className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg"
                >
                  {loading ? 'Generando...' : 'Generar Código'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
