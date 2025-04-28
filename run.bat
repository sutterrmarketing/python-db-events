@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Set container and image names
set BACKEND_CNAME=backend_container
set BACKEND_INAME=backend_image
set BACKEND_PORT=8000
set BACKEND_DATA_DIR=%cd%\app\data

set FRONTEND_CNAME=front_container
set FRONTEND_INAME=front_image
set FRONTEND_PORT=3000

set EXTERNAL_PORT=3000

set NETWORK_NAME=web-network

REM Stop and remove the existing containers if they are running
docker stop %BACKEND_CNAME%
docker rm %BACKEND_CNAME%
docker stop %FRONTEND_CNAME%
docker rm %FRONTEND_CNAME%

REM Clean up unused docker resources
docker system prune -af

REM Build backend image
docker build --no-cache -t %BACKEND_INAME% -f ./image/DockerFile.backend .

REM Prune dangling images
docker image prune -f

REM Build frontend image
docker build --no-cache ^
  -t %FRONTEND_INAME% ^
  -f ./image/DockerFile.frontend ^
  --build-arg NEXT_PUBLIC_API_URL=http://backend_container:8000 .

REM Prune dangling images
docker image prune -f

REM Create network if it does not exist
docker network inspect %NETWORK_NAME% >nul 2>&1
if errorlevel 1 (
  docker network create %NETWORK_NAME%
)

REM Run backend container
docker run -d ^
  --name %BACKEND_CNAME% ^
  --network %NETWORK_NAME% ^
  -p %BACKEND_PORT%:%BACKEND_PORT% ^
  -v "%BACKEND_DATA_DIR%:/code/app/data" ^
  %BACKEND_INAME%

REM Run frontend container
docker run -d ^
  --name %FRONTEND_CNAME% ^
  --network %NETWORK_NAME% ^
  -p %EXTERNAL_PORT%:%FRONTEND_PORT% ^
  %FRONTEND_INAME%

echo.
echo Containers are up and running!
ENDLOCAL
pause