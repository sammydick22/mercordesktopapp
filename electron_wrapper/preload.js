// Preload script runs in isolated context
window.addEventListener('DOMContentLoaded', () => {
  console.log('TimeTracker Desktop App loaded');
  
  // You can expose secure APIs to the renderer process here if needed
  // window.electronAPI = {
  //   someFunction: () => {}
  // }
});
