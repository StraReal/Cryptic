// Type definitions for Electron renderer process
export interface IpcRendererApi {
  invoke: (channel: string, data?: any) => Promise<any>;
  on: (channel: string, listener: (event: any, ...args: any[]) => void) => void;
  off: (channel: string, listener?: (...args: any[]) => void) => void;
  send: (channel: string, ...args: any[]) => void;
}

declare global {
  interface Window {
    ipcRenderer: IpcRendererApi;
  }
}
