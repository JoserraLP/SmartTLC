@ECHO OFF
FOR /f "tokens=*" %%i IN ('docker volume ls -aq') DO docker rm %%i