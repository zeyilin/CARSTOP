*** To build the cscope.files ***
cd /
find /path/to/src/ -name '*.c' -o -name '*.h' > /path/to/cscope/dir/cscope.files

*** To build the cscope database ***
cd /path/to/cscope/dir/
cscope -b -q
