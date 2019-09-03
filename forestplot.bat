
@echo off

if ["%~1"] == [""] goto blank



docker run -it --rm -v %1:/tmp/project forestplot python3.7 forestplots.py /tmp/project




goto done

:blank


echo Usage: %0 [DIRECTORY OF PDFs]

:done