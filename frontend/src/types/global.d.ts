/**
 * Global type declarations for the frontend
 */

declare global {
  interface Window {
    openIntegrationModal: (integrationType: string) => void;
  }
}

export {};
