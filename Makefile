maketyperwiter: backend.c
	gcc -fPIC -shared -I/usr/local/lib -lbcm2835 -O2 -o libtypewriter.so backend.c /usr/local/lib/libbcm2835.a
