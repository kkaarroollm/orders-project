/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_ORDERS: string;
  // You can add more env vars as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
