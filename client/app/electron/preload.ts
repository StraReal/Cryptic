import { ipcRenderer, contextBridge } from "electron";

// --------- Expose some API to the Renderer process ---------
// contextBridge.exposeInMainWorld("ipcRenderer", {
//   on(...args: Parameters<typeof ipcRenderer.on>) {
//     const [channel, listener] = args;
//     return ipcRenderer.on(channel, (event, ...args) =>
//       listener(event, ...args)
//     );
//   },
//   off(...args: Parameters<typeof ipcRenderer.off>) {
//     const [channel, ...omit] = args;
//     return ipcRenderer.off(channel, ...omit);
//   },
//   send(...args: Parameters<typeof ipcRenderer.send>) {
//     const [channel, ...omit] = args;
//     return ipcRenderer.send(channel, ...omit);
//   },
//   invoke(...args: Parameters<typeof ipcRenderer.invoke>) {
//     const [channel, ...omit] = args;
//     return ipcRenderer.invoke(channel, ...omit);
//   },

//   // You can expose other APTs you need here.
//   // ...
// });

contextBridge.exposeInMainWorld("ipcRenderer", {
  invoke: (channel: string, ...args: any[]) =>
    ipcRenderer.invoke(channel, ...args),
  send: (channel: string, ...args: any[]) => ipcRenderer.send(channel, ...args),
  on: (channel: string, listener: (...args: any[]) => void) => {
    ipcRenderer.on(channel, listener);
  },
  once: (channel: string, listener: (...args: any[]) => void) => {
    ipcRenderer.once(channel, listener);
  },
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel);
  },
  removeListener: (channel: string, listener: (...args: any[]) => void) => {
    ipcRenderer.removeListener(channel, listener);
  },
});
