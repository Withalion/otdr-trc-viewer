import zlib,sys
def stream(fn):
    d=open(fn,'rb').read(); i=0; out=b''
    while True:
        j=d.find(b'x\xda',i)
        if j<0: break
        try:
            do=zlib.decompressobj(); o=do.decompress(d[j:]); out+=o; i=len(d)-len(do.unused_data)
        except: i=j+2
    return out
if __name__=="__main__":
    open(sys.argv[2],'wb').write(stream(sys.argv[1]))
