module.exports = {
  apps: [
    {
      name: 'financehub-backend',
      script: 'C:\\Projects\\VTB_API_HACK\\backend\\venv\\Scripts\\python.exe',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      cwd: 'C:\\Projects\\VTB_API_HACK\\backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      error_file: 'logs/backend-error.log',
      out_file: 'logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    },
    // Uncomment if GOST service is configured
    // {
    //   name: 'financehub-gost',
    //   script: 'C:\\Projects\\VTB_API_HACK\\gost_windows_service.py',
    //   interpreter: 'python',
    //   cwd: 'C:\\Projects\\VTB_API_HACK',
    //   instances: 1,
    //   autorestart: true,
    //   watch: false,
    //   env: {
    //     PYTHONUNBUFFERED: '1',
    //   },
    // },
  ],
};

