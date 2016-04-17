@echo off

rem by Lieven Paulissen, based on Guido Tack's mzn-gecode.bat

setlocal
minizinc -Glinear -b mip %*
